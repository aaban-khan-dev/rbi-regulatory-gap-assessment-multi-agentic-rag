"""Naive top-k cosine search over all chunks (both corpora, no filters).

    .\\.venv\\Scripts\\python.exe scripts\\query.py "your question" --k 10
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from regassess.db import get_connection  # noqa: E402
from regassess.embeddings import embed_query  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("query")
    parser.add_argument("--k", type=int, default=10)
    args = parser.parse_args()

    qvec = embed_query(args.query)

    # <=> is pgvector's cosine distance, so similarity = 1 - distance.
    sql = (
        "SELECT corpus, doc_id, clause_path, text, 1 - (embedding <=> %s) AS score "
        "FROM chunks ORDER BY embedding <=> %s LIMIT %s"
    )
    with get_connection() as conn:
        rows = conn.execute(sql, (qvec, qvec, args.k)).fetchall()

    print(f"Query: {args.query}\n")
    for rank, (corpus, doc_id, path, text, score) in enumerate(rows, 1):
        snippet = " ".join(text.split())[:150]
        print(f"{rank:>2}. {score:.4f}  {corpus:<10} {doc_id}  [{path}]")
        print(f"    {snippet}")


if __name__ == "__main__":
    main()
