"""Local embeddings with bge-small-en-v1.5 (384 dimensions, CPU only)."""

from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from regassess.config import settings

# bge is trained so that *queries* carry this instruction and passages do not.
# Skipping it on queries measurably hurts retrieval; adding it to passages is wrong.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    # Loaded once per process; device is pinned so a stray GPU never changes results.
    return SentenceTransformer(settings.embedding_model, device="cpu")


def embed_texts(texts: list[str], batch_size: int = 32) -> np.ndarray:
    """Embed passages. Returns an (n, 384) float32 array of unit vectors.

    Unit-length vectors make cosine similarity equal to the dot product.
    """
    return _model().encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=len(texts) > batch_size,
    ).astype(np.float32)


def embed_query(query: str) -> np.ndarray:
    """Embed one search query (with the bge instruction prefix). Shape (384,)."""
    return embed_texts([QUERY_PREFIX + query])[0]
