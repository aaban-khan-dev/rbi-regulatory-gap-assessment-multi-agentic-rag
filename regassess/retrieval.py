"""Retrieval over the chunk store: naive cosine search, BM25 keyword search, and
their Reciprocal Rank Fusion."""

import re
from functools import lru_cache

from rank_bm25 import BM25Okapi

from regassess.config import settings
from regassess.db import get_connection
from regassess.embeddings import embed_query, passage_text
from regassess.stopwords import ENGLISH_STOPWORDS

# BM25 parameters are passed explicitly (these equal rank_bm25's defaults) so that
# what a run used is written down in the code and the run file, not left implicit in
# a library default. They are not tuned against the gold set.
BM25_K1 = 1.5
BM25_B = 0.75
BM25_EPSILON = 0.25

# A comma-joined digit group ("2,00,000", "10,000") is ONE token; everything else is a
# run of letters/digits. Without the first alternative "Rs.2,00,000" becomes
# rs/2/00/000 and an exact amount carries no IDF signal. No stemming, no stopwords.
_TOKEN = re.compile(r"\d+(?:,\d+)+|[a-z0-9]+")
TOKENIZER = "lowercase; token = comma-joined digit group (2,00,000) or [a-z0-9]+ run; no stemming, no stopwords"


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


TOKENIZER_NOSTOP = TOKENIZER + "; then NLTK English stopwords removed from query and documents"


def tokenize(text: str, drop_stopwords: bool = False) -> list[str]:
    tokens = _TOKEN.findall(text.lower())
    if drop_stopwords:
        tokens = [t for t in tokens if t not in ENGLISH_STOPWORDS]
    return tokens


@lru_cache(maxsize=None)
def _bm25_index(corpus: str, drop_stopwords: bool = False) -> tuple[list[str], BM25Okapi]:
    """One in-memory BM25 index per corpus, built from Postgres on first use.

    It indexes passage_text(), the same function build_index.py embeds, so BM25 and the
    embeddings see identical text (plain `text`, or context + text when PARENT_CONTEXT
    is on). Per-corpus because every query is scoped to one corpus, so IDF should come
    from that corpus alone. Rebuild the process after re-indexing. The stopword flag is
    part of the cache key, so the two tokenizations never share an index.
    """
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT chunk_id, text, context FROM chunks WHERE corpus = %s ORDER BY chunk_id", (corpus,)
        ).fetchall()
    ids = [r[0] for r in rows]
    docs = [tokenize(passage_text({"text": r[1], "context": r[2]}), drop_stopwords) for r in rows]
    return ids, BM25Okapi(docs, k1=BM25_K1, b=BM25_B, epsilon=BM25_EPSILON)


def keyword_search(query: str, k: int, corpus: str, drop_stopwords: bool = False) -> list[dict]:
    """Top-k chunks by BM25, best first, ties broken by chunk_id.

    `query` is the raw query. The bge instruction prefix is added inside embed_query()
    and never reaches here. Chunks sharing no token with the query score 0 and are left
    out: they carry no ranking information.
    """
    ids, index = _bm25_index(corpus, drop_stopwords)
    tokens = tokenize(query, drop_stopwords)
    if not tokens:
        return []
    scores = index.get_scores(tokens)
    ranked = sorted(zip(ids, scores), key=lambda p: (-p[1], p[0]))
    return [{"chunk_id": cid, "score": float(s)} for cid, s in ranked[:k] if s > 0]


def rrf_fuse(rankings: list[list[str]], k: int) -> list[dict]:
    """Reciprocal Rank Fusion: score(chunk) = sum over lists of 1 / (k + rank), rank from 1.

    A chunk missing from a list adds nothing for that list. Ties are broken by chunk_id
    so the fused order is deterministic.
    """
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, cid in enumerate(ranking, start=1):
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
    fused = sorted(scores.items(), key=lambda p: (-p[1], p[0]))
    return [{"chunk_id": cid, "score": s} for cid, s in fused]


def hybrid_search(query: str, k: int, corpus: str, drop_stopwords: bool = False) -> list[dict]:
    """Vector search and BM25 over `corpus`, fused by RRF. Returns the top k, best first.

    Stopwords affect only the BM25 side; the vector side always gets the full query.
    """
    pool = settings.rrf_candidates
    vector_ids = [r["chunk_id"] for r in search(query, k=pool, corpus=corpus)]
    keyword_ids = [r["chunk_id"] for r in keyword_search(query, k=pool, corpus=corpus, drop_stopwords=drop_stopwords)]
    return rrf_fuse([vector_ids, keyword_ids], settings.rrf_k)[:k]


def bm25_config(drop_stopwords: bool = False) -> dict:
    """BM25 settings alone (no fusion), for the run file of a keyword-only variant."""
    return {
        "bm25_k1": BM25_K1,
        "bm25_b": BM25_B,
        "bm25_epsilon": BM25_EPSILON,
        "tokenizer": TOKENIZER_NOSTOP if drop_stopwords else TOKENIZER,
    }


def hybrid_config(drop_stopwords: bool = False) -> dict:
    """Everything that changes hybrid numbers, for the run file."""
    return {
        "rrf_k": settings.rrf_k,
        "rrf_candidates": settings.rrf_candidates,
        "bm25_k1": BM25_K1,
        "bm25_b": BM25_B,
        "bm25_epsilon": BM25_EPSILON,
        "tokenizer": TOKENIZER_NOSTOP if drop_stopwords else TOKENIZER,
    }
