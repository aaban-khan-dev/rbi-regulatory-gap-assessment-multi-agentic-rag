"""Retrieval metrics. Pure functions: no database, no model calls.

Every function takes a ranked list of chunk_ids (best first) and the item's
gold or stale set. Definitions are in docs/EVALUATION.md.
"""

import math

CATEGORIES = ("straightforward", "paraphrased", "version_sensitive", "repealed_document")
METRICS = ("recall", "mrr", "ndcg", "stale_rate")


def recall_at_k(ranked: list[str], gold: list[str], k: int) -> float:
    """Fraction of the item's gold chunks found in the top k."""
    top = set(ranked[:k])
    return sum(1 for g in set(gold) if g in top) / len(set(gold))


def reciprocal_rank(ranked: list[str], gold: list[str], k: int) -> float:
    """1 / rank of the first gold chunk within the top k, else 0."""
    gold_set = set(gold)
    for rank, cid in enumerate(ranked[:k], start=1):
        if cid in gold_set:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(ranked: list[str], gold: list[str], k: int) -> float:
    """Binary-relevance nDCG: gain 1 for a gold chunk, discounted by log2(rank + 1)."""
    gold_set = set(gold)
    dcg = sum(1.0 / math.log2(rank + 1) for rank, cid in enumerate(ranked[:k], start=1) if cid in gold_set)
    # Best possible: every gold chunk (up to k of them) at the top.
    ideal = sum(1.0 / math.log2(rank + 1) for rank in range(1, min(len(gold_set), k) + 1))
    return dcg / ideal


def stale_hit(ranked: list[str], stale: list[str], k: int) -> int:
    """1 if any stale chunk appears in the top k, else 0."""
    return int(bool(set(stale) & set(ranked[:k])))


def score_item(ranked: list[str], gold: list[str], stale: list[str], k: int) -> dict:
    """The four numbers for one item. stale_rate is None when the item has no stale set."""
    return {
        "recall": recall_at_k(ranked, gold, k),
        "mrr": reciprocal_rank(ranked, gold, k),
        "ndcg": ndcg_at_k(ranked, gold, k),
        "stale_rate": stale_hit(ranked, stale, k) if stale else None,
    }


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def aggregate(scores: list[dict]) -> dict:
    """Equal-weight mean per metric. stale_rate averages only over items that have
    a stale set; n_stale says how many that is."""
    out = {m: _mean([s[m] for s in scores if s[m] is not None]) for m in METRICS}
    out["n"] = len(scores)
    out["n_stale"] = sum(1 for s in scores if s["stale_rate"] is not None)
    return out


def summarize(items: list[dict], k: int) -> dict:
    """Score a run's items. Each item needs category, gold_chunk_ids, stale_chunk_ids
    and ranking (a list of [chunk_id, score]). Returns per-item scores, overall and
    per-category aggregates."""
    per_item = {
        it["item_id"]: score_item(
            [cid for cid, _ in it["ranking"]], it["gold_chunk_ids"], it.get("stale_chunk_ids", []), k
        )
        for it in items
    }
    by_category = {
        cat: aggregate([per_item[it["item_id"]] for it in items if it["category"] == cat]) for cat in CATEGORIES
    }
    return {"per_item": per_item, "overall": aggregate(list(per_item.values())), "by_category": by_category}
