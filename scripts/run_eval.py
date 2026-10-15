"""Run one retrieval variant over the gold set and save the raw rankings.

    .\\.venv\\Scripts\\python.exe scripts\\run_eval.py --variant naive --k 10

Makes no LLM calls. The run file keeps every item's ranked list (to --depth), so
new metrics can be computed later without re-running retrieval.
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from regassess.config import settings  # noqa: E402
from regassess.evaluation import CATEGORIES, summarize  # noqa: E402
from regassess.variants import VARIANT_CONFIG, VARIANTS  # noqa: E402

GOLD_PATH = settings.data_dir / "eval" / "gold_set.yaml"
RUNS_DIR = settings.data_dir / "eval" / "runs"


def fmt(value: float | None) -> str:
    return "  n/a" if value is None else f"{value:.3f}"


def print_table(summary: dict, k: int) -> None:
    header = f"{'':<20}{'n':>4}  {f'recall@{k}':>9}  {'MRR':>6}  {f'nDCG@{k}':>7}  {'stale_rate':>10}  {'(n_stale)':>9}"
    print(header)
    print("-" * len(header))
    rows = [("OVERALL", summary["overall"])] + [(c, summary["by_category"][c]) for c in CATEGORIES]
    for name, a in rows:
        print(
            f"{name:<20}{a['n']:>4}  {fmt(a['recall']):>9}  {fmt(a['mrr']):>6}  {fmt(a['ndcg']):>7}  "
            f"{fmt(a['stale_rate']):>10}  {a['n_stale']:>9}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--variant", default="naive", choices=sorted(VARIANTS))
    parser.add_argument("--k", type=int, default=10, help="cutoff the metrics are computed at")
    parser.add_argument("--depth", type=int, default=50, help="how many ranked chunks to store per item")
    args = parser.parse_args()
    if args.depth < args.k:
        parser.error("--depth must be at least --k")

    gold_bytes = GOLD_PATH.read_bytes()
    gold_items = yaml.safe_load(gold_bytes)["items"]
    retrieve = VARIANTS[args.variant]

    items = []
    for n, g in enumerate(gold_items, start=1):
        ranked = retrieve(g["query"], g.get("as_of"), g["corpus"], args.depth)
        items.append(
            {
                "item_id": g["item_id"],
                "category": g["category"],
                "corpus": g["corpus"],
                "query": g["query"],
                "as_of": g.get("as_of"),
                "gold_chunk_ids": g["gold_chunk_ids"],
                "stale_chunk_ids": g.get("stale_chunk_ids", []),
                "ranking": [[r["chunk_id"], round(float(r["score"]), 6)] for r in ranked],
            }
        )
        print(f"\r{n}/{len(gold_items)} queries", end="", file=sys.stderr)
    print(file=sys.stderr)

    started = datetime.now()
    run = {
        "variant": args.variant,
        "k": args.k,
        "depth": args.depth,
        "embedding_model": settings.embedding_model,
        "query_prefix": settings.query_prefix,
        "parent_context": settings.parent_context,
        "variant_config": VARIANT_CONFIG.get(args.variant, lambda: {})(),
        "gold_sha256": hashlib.sha256(gold_bytes).hexdigest(),
        "timestamp": started.isoformat(timespec="seconds"),
        "items": items,
    }
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = RUNS_DIR / f"{args.variant}_{started:%Y%m%d-%H%M%S}.json"
    path.write_text(json.dumps(run, indent=1), encoding="utf-8")

    summary = summarize(items, args.k)
    print(f"variant={args.variant} k={args.k} depth={args.depth} model={settings.embedding_model}")
    print(f"query_prefix={settings.query_prefix!r}  parent_context={settings.parent_context}")
    if run["variant_config"]:
        print(f"variant_config={run['variant_config']}")
    print(f"gold_sha256={run['gold_sha256'][:16]}...  saved {path.relative_to(settings.project_root)}\n")
    print_table(summary, args.k)
    print("\nstale_rate averages only over items that have stale_chunk_ids (n_stale).")

    # Sort by recall, then item_id, so ties are stable. Many items tie at 0.
    scored = sorted(items, key=lambda it: (summary["per_item"][it["item_id"]]["recall"], it["item_id"]))
    zeros = sum(1 for it in items if summary["per_item"][it["item_id"]]["recall"] == 0)
    print(f"\n{zeros} of {len(items)} items have recall@{args.k} = 0. 10 worst by recall (ties broken by item_id):")
    for it in scored[:10]:
        s = summary["per_item"][it["item_id"]]
        print(f"  {it['item_id']}  {it['category']:<18} recall={s['recall']:.2f}  {it['query']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
