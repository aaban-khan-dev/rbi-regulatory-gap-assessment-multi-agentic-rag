"""Show why items scored recall@k = 0 in a saved eval run. Read-only, no LLM calls.

    .\\.venv\\Scripts\\python.exe scripts\\diagnose_zeros.py [--run PATH] [--item G-004]

For each zero-recall item: the gold chunks with their rank in the stored ranking
and their opening text, and the top 3 chunks actually retrieved. Classes (a) near
miss and (b) far miss are assigned here from the ranking. (c) label problem and
(d) chunking problem need a reader; the chunk length is printed as a hint for (d).
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from regassess.config import settings  # noqa: E402
from regassess.db import get_connection  # noqa: E402
from regassess.evaluation import recall_at_k  # noqa: E402

RUNS_DIR = settings.data_dir / "eval" / "runs"


def one_line(text: str, n: int) -> str:
    return " ".join(text.split())[:n]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", type=Path, help="run file (default: the most recent in data/eval/runs)")
    parser.add_argument("--item", help="show only this item_id")
    args = parser.parse_args()

    path = args.run or max(RUNS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
    run = json.loads(path.read_text(encoding="utf-8"))
    k = run["k"]
    print(f"run: {path.name}  variant={run['variant']} k={k} depth={run['depth']}\n")

    zeros = [
        it for it in run["items"] if recall_at_k([c for c, _ in it["ranking"]], it["gold_chunk_ids"], k) == 0
    ]
    if args.item:
        zeros = [it for it in zeros if it["item_id"] == args.item]

    # One query for every chunk we will mention.
    needed = {c for it in zeros for c in it["gold_chunk_ids"] + [c for c, _ in it["ranking"][:3]]}
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT chunk_id, doc_id, clause_path, text FROM chunks WHERE chunk_id = ANY(%s)", (sorted(needed),)
        ).fetchall()
    chunks = {r[0]: {"doc_id": r[1], "path": r[2], "text": r[3]} for r in rows}

    classes: dict[str, list[str]] = {}
    for it in zeros:
        ids = [c for c, _ in it["ranking"]]
        ranks = {g: (ids.index(g) + 1 if g in ids else None) for g in it["gold_chunk_ids"]}
        # Auto class: near if any gold chunk is ranked 11..depth, else far.
        auto = "a near miss" if any(r is not None for r in ranks.values()) else "b far miss"
        classes.setdefault(auto[0], []).append(it["item_id"])

        print("=" * 100)
        print(f"{it['item_id']}  {it['category']}  as_of={it['as_of']}  [{auto}]")
        print(f"query: {it['query']}")
        for g, rank in ranks.items():
            c = chunks[g]
            where = f"rank {rank}" if rank else f"not in top {run['depth']}"
            print(f"  GOLD {g}  path={c['path']}  {len(c['text'])} chars  -> {where}")
            print(f"       {one_line(c['text'], 200)}")
        print("  retrieved top 3:")
        for cid, score in it["ranking"][:3]:
            c = chunks[cid]
            print(f"    {cid}  path={c['path']}  score={score:.3f}  {len(c['text'])} chars")
            print(f"       {one_line(c['text'], 100)}")

    print("=" * 100)
    counts = Counter({k_: len(v) for k_, v in classes.items()})
    print(f"{len(zeros)} zero-recall items. Automatic split: near miss (a) {counts['a']}, far miss (b) {counts['b']}")
    print("(c) label problem and (d) chunking problem are judged by reading the output above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
