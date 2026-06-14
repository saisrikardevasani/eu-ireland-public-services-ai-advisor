"""Text embedder using sentence-transformers.

Wraps the model as a singleton so we only load it once (loading takes ~2 seconds on CPU).

Local dev default: BAAI/bge-small-en-v1.5 (134 MB, 384-dim)
Production:        BAAI/bge-m3             (2.2 GB, 1024-dim) — update EMBEDDING_DIM too

bge models are trained to produce L2-normalized embeddings when you pass
normalize_embeddings=True, which makes cosine similarity == dot product and
improves retrieval quality slightly.
"""

import logging

from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger(__name__)

# Module-level singleton — loaded once on first use
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("Loading embedding model: %s", settings.embedding_model)
        _model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded (dim=%d)", settings.embedding_dim)
    return _model


def embed_texts(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """Return L2-normalized embeddings for each text.

    batch_size=32 is a good default for CPU inference.
    Increase for GPU (e.g. 128).
    """
    model = _get_model()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=len(texts) > 100,
    )
    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    """Embed a single query string."""
    return embed_texts([query])[0]
