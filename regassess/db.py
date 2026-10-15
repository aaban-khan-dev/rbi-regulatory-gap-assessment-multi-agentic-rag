"""Postgres connection handling and schema for the chunk store."""

import psycopg
from pgvector.psycopg import register_vector

from regassess.config import settings

EMBEDDING_DIM = 384  # bge-small-en-v1.5

# Everything we may want to filter on later (corpus, status, dates, doc type) is a
# real column, not JSON. No ANN index on purpose: at ~700 rows an exact scan is
# instant and keeps the naive baseline exact.
_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id       TEXT PRIMARY KEY,
    corpus         TEXT NOT NULL CHECK (corpus IN ('regulation', 'internal')),
    doc_id         TEXT NOT NULL,
    clause_path    TEXT,
    text           TEXT NOT NULL,
    context        TEXT,
    embedding     vector({EMBEDDING_DIM}) NOT NULL,
    status         TEXT,
    effective_from DATE,
    effective_to   DATE,
    document_type  TEXT,
    amends         TEXT,
    page_start     INT,
    page_end       INT
);
-- context was added after the first index build; CREATE TABLE IF NOT EXISTS would skip it.
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS context TEXT;
CREATE INDEX IF NOT EXISTS chunks_corpus_idx ON chunks (corpus);
CREATE INDEX IF NOT EXISTS chunks_doc_id_idx ON chunks (doc_id);
"""

COLUMNS = (
    "chunk_id", "corpus", "doc_id", "clause_path", "text", "context", "embedding", "status",
    "effective_from", "effective_to", "document_type", "amends", "page_start",
    "page_end",
)


def get_connection() -> psycopg.Connection:
    """Open a connection with the pgvector type registered.

    The extension must exist before register_vector can look up its type, so
    it is created on a throwaway connection first (idempotent).
    """
    with psycopg.connect(settings.database_url, autocommit=True) as boot:
        boot.execute("CREATE EXTENSION IF NOT EXISTS vector")
    conn = psycopg.connect(settings.database_url)
    register_vector(conn)
    return conn


def init_schema(conn: psycopg.Connection) -> None:
    conn.execute(_SCHEMA)
    conn.commit()
