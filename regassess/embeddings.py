"""Local embeddings with bge-small-en-v1.5 (384 dimensions, CPU only)."""

from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from regassess.config import settings

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


def passage_text(chunk: dict) -> str:
    """What a chunk is embedded as: its verbatim text, or, when settings.parent_context
    is on, its parent-heading context line first.

    `text` itself is never altered, so citations quote the source exactly.
    """
    if settings.parent_context and chunk.get("context"):
        return f"{chunk['context']}\n{chunk['text']}"
    return chunk["text"]


def embed_query(query: str) -> np.ndarray:
    """Embed one search query with settings.query_prefix (the bge instruction). Shape (384,)."""
    return embed_texts([settings.query_prefix + query])[0]
