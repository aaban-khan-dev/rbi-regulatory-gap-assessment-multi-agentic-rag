"""Embed every chunk from both corpora and load them into Postgres.

Re-runnable: the whole table is replaced inside one transaction, so a failure
part-way leaves the previous index untouched.

    .\\.venv\\Scripts\\python.exe scripts\\build_index.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from regassess.chunking_internal import chunk_all_policies  # noqa: E402
from regassess.config import settings  # noqa: E402
from regassess.db import COLUMNS, get_connection, init_schema  # noqa: E402
from regassess.embeddings import embed_texts, passage_text  # noqa: E402


def load_regulation_chunks() -> list[dict]:
    """Read the Phase 2 jsonl files. Files starting with '_' are build artefacts."""
    chunks = []
    for path in sorted(settings.processed_dir.glob("*.jsonl")):
        if path.name.startswith("_"):
            continue
        with path.open(encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                rec["corpus"] = "regulation"
                chunks.append(rec)
    return chunks


def main() -> None:
    chunks = load_regulation_chunks() + chunk_all_policies()
    if not chunks:
        sys.exit("No chunks found. Run scripts/build_chunks.py first.")

    print(f"Embedding {len(chunks)} chunks (CPU, batched)...")
    vectors = embed_texts([passage_text(c) for c in chunks])

    # Column order comes from db.COLUMNS so INSERT and row tuples cannot drift apart.
    placeholders = ", ".join(["%s"] * len(COLUMNS))
    sql = f"INSERT INTO chunks ({', '.join(COLUMNS)}) VALUES ({placeholders})"
    rows = [
        tuple(vec if col == "embedding" else c.get(col) for col in COLUMNS)
        for c, vec in zip(chunks, vectors)
    ]

    with get_connection() as conn:
        init_schema(conn)
        with conn.transaction():
            conn.execute("TRUNCATE chunks")
            with conn.cursor() as cur:
                cur.executemany(sql, rows)

        print("Loaded:")
        for corpus, n, docs in conn.execute(
            "SELECT corpus, count(*), count(DISTINCT doc_id) FROM chunks "
            "GROUP BY corpus ORDER BY corpus"
        ):
            print(f"  {corpus:<11} {n:>5} chunks  {docs:>3} documents")


if __name__ == "__main__":
    main()
