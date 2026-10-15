"""Print saved eval runs side by side as an ablation table.

    .\\.venv\\Scripts\\python.exe scripts\\compare_runs.py data\\eval\\runs\\naive_*.json data\\eval\\runs\\hybrid_*.json

Metrics are recomputed from the stored rankings, not read from the run file.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from regassess.evaluation import CATEGORIES, summarize  # noqa: E402

METRIC_LABELS = (("recall", "recall"), ("mrr", "MRR"), ("ndcg", "nDCG"), ("stale_rate", "stale_rate"))


def fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("runs", nargs="+", type=Path, help="run files written by run_eval.py")
    parser.add_argument("--k", type=int, help="score every run at this cutoff instead of its own k (at most its stored depth)")
    args = parser.parse_args()

    runs = [json.loads(p.read_text(encoding="utf-8")) for p in args.runs]
    if args.k:
        for r in runs:
            if args.k > r["depth"]:
                parser.error(f"--k {args.k} exceeds the stored depth {r['depth']} of a run")
            r["k"] = args.k
    summaries = [summarize(r["items"], r["k"]) for r in runs]

    # Different gold sets or cutoffs make the columns incomparable; say so loudly.
    for field, label in (("gold_sha256", "gold set"), ("k", "k"), ("embedding_model", "embedding model"), ("query_prefix", "query prefix"), ("parent_context", "parent_context flag")):
        if len({json.dumps(r.get(field)) for r in runs}) > 1:
            print(f"WARNING: runs differ in {label}; columns are not directly comparable.\n")

    # Two runs of the same variant with different settings (e.g. rrf_k) are not
    # comparable as "the same configuration". Older runs have no variant_config.
    by_variant: dict[str, set[str]] = {}
    for r in runs:
        by_variant.setdefault(r["variant"], set()).add(json.dumps(r.get("variant_config", {}), sort_keys=True))
    for variant, configs in by_variant.items():
        if len(configs) > 1:
            print(f"WARNING: runs of variant '{variant}' differ in variant_config; they are not the same configuration.\n")

    # Column labels: the file name without its trailing timestamp, so a renamed run
    # (naive_preheadings_<ts>.json) reads as "naive_preheadings" next to "naive".
    labels = [re.sub(r"_\d{8}-\d{6}$", "", p.stem) for p in args.runs]
    width = max(12, *(len(label) for label in labels)) + 2
    k = runs[0]["k"]

    print(f"k={k}. stale_rate averages only over items with a stale set (n_stale in each block header).\n")
    sections = [("OVERALL", lambda s: s["overall"])] + [(c, lambda s, c=c: s["by_category"][c]) for c in CATEGORIES]
    print(f"{'':<26}" + "".join(f"{label:>{width}}" for label in labels))
    for title, pick in sections:
        print(f"\n{title}  (n={pick(summaries[0])['n']}, n_stale={pick(summaries[0])['n_stale']})")
        for key, name in METRIC_LABELS:
            row = "".join(f"{fmt(pick(s)[key]):>{width}}" for s in summaries)
            print(f"  {name + ('@' + str(k) if key in ('recall', 'ndcg') else ''):<24}{row}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
