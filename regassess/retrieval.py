"""Naive top-k cosine search over the chunk store."""

from regassess.db import get_connection
from regassess.embeddings import embed_query


def search(query: str, k: int = 10, corpus: str | None = None) -> list[dict]:
    """Return the k chunks nearest to `query`, best first.

    corpus=None searches both corpora; 'regulation' or 'internal' restricts the scan.
    """
    qvec = embed_query(query)

    # <=> is pgvector's cosine distance, so similarity = 1 - distance.
    where = "WHERE corpus = %s " if corpus else ""
    params: tuple = (qvec, corpus, qvec, k) if corpus else (qvec, qvec, k)
    sql = (
        "SELECT chunk_id, corpus, doc_id, clause_path, text, 1 - (embedding <=> %s) AS score "
        f"FROM chunks {where}ORDER BY embedding <=> %s LIMIT %s"
    )
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    keys = ("chunk_id", "corpus", "doc_id", "clause_path", "text", "score")
    return [dict(zip(keys, row)) for row in rows]
