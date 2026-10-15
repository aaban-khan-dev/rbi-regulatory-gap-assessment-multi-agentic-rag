"""Retrieval configurations the evaluation harness can run.

A variant is a function (query, as_of, corpus, depth) -> ranked list of
{"chunk_id", "score"}, best first. Adding a configuration in a later phase means
writing one function and one entry in VARIANTS; the harness is not touched.
"""

from typing import Callable

from regassess.retrieval import search


def naive(query: str, as_of: str | None, corpus: str, depth: int) -> list[dict]:
    """Phase 4 baseline: top-k cosine over the item's corpus.

    as_of is accepted and deliberately ignored. No date filtering is the baseline,
    which is why this variant's stale rate is expected to be bad.
    """
    return [{"chunk_id": r["chunk_id"], "score": r["score"]} for r in search(query, k=depth, corpus=corpus)]


VARIANTS: dict[str, Callable[[str, str | None, str, int], list[dict]]] = {
    "naive": naive,
}
