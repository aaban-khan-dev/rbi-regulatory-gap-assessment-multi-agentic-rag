"""Naive top-k cosine search over all chunks (both corpora, no filters).

    .\\.venv\\Scripts\\python.exe scripts\\query.py "your question" --k 10
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from regassess.retrieval import search  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("query")
    parser.add_argument("--k", type=int, default=10)
    args = parser.parse_args()

    hits = search(args.query, k=args.k)

    print(f"Query: {args.query}\n")
    for rank, h in enumerate(hits, 1):
        snippet = " ".join(h["text"].split())[:150]
        print(f"{rank:>2}. {h['score']:.4f}  {h['corpus']:<10} {h['doc_id']}  [{h['clause_path']}]")
        print(f"    {snippet}")


if __name__ == "__main__":
    main()
