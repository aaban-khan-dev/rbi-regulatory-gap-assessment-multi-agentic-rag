"""Retrieval configurations the evaluation harness can run.

A variant is a function (query, as_of, corpus, depth) -> ranked list of
{"chunk_id", "score"}, best first. Adding a configuration in a later phase means
writing one function and one entry in VARIANTS; the harness is not touched.
"""

from typing import Callable

from regassess.retrieval import bm25_config, hybrid_config, hybrid_search, keyword_search, search


def naive(query: str, as_of: str | None, corpus: str, depth: int) -> list[dict]:
    """Phase 4 baseline: top-k cosine over the item's corpus.

    as_of is accepted and deliberately ignored. No date filtering is the baseline,
    which is why this variant's stale rate is expected to be bad.
    """
    return [{"chunk_id": r["chunk_id"], "score": r["score"]} for r in search(query, k=depth, corpus=corpus)]


def hybrid(query: str, as_of: str | None, corpus: str, depth: int) -> list[dict]:
    """Phase 8: vector + BM25, fused by RRF. as_of is ignored, as in naive: no date
    logic until Phase 10, so stale_rate is not expected to move."""
    return hybrid_search(query, k=depth, corpus=corpus)


def bm25_only(query: str, as_of: str | None, corpus: str, depth: int) -> list[dict]:
    """Keyword search alone, no fusion: does the BM25 list carry any signal by itself?

    Chunks sharing no token with the query are excluded, so a ranking can be shorter than
    depth. as_of is ignored."""
    return keyword_search(query, k=depth, corpus=corpus)


def hybrid_nostop(query: str, as_of: str | None, corpus: str, depth: int) -> list[dict]:
    """The hybrid variant with NLTK English stopwords removed on the BM25 side (query and
    documents). The vector side is untouched. Its own ablation row; `hybrid` is unchanged."""
    return hybrid_search(query, k=depth, corpus=corpus, drop_stopwords=True)


VARIANTS: dict[str, Callable[[str, str | None, str, int], list[dict]]] = {
    "naive": naive,
    "hybrid": hybrid,
    "bm25_only": bm25_only,
    "hybrid_nostop": hybrid_nostop,
}

# Settings that change a variant's numbers, written into every run file. A variant with
# nothing to record is absent.
VARIANT_CONFIG: dict[str, Callable[[], dict]] = {
    "hybrid": hybrid_config,
    "bm25_only": bm25_config,
    "hybrid_nostop": lambda: hybrid_config(drop_stopwords=True),
}
