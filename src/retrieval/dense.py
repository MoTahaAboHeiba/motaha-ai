"""
src/retrieval/dense.py

Dense vector retrieval against Qdrant Cloud using FastEmbed.

The embedding model (BAAI/bge-small-en-v1.5, ONNX backend) and the Qdrant
client are each lazily initialised on first call and then reused for the
lifetime of the process.
"""

import logging
from typing import Any

from fastembed import TextEmbedding
from qdrant_client import QdrantClient

from src.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "motaha-ai"
MODEL_NAME = "BAAI/bge-small-en-v1.5"

_embedding_model: TextEmbedding | None = None
_client: QdrantClient | None = None


def _get_embedding_model() -> TextEmbedding:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = TextEmbedding(model_name=MODEL_NAME)
        logger.info("FastEmbed model loaded: %s", MODEL_NAME)
    return _embedding_model


def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )
        logger.info("Qdrant client connected to %s", settings.QDRANT_URL)
    return _client


def search(
    query: str,
    top_k: int = 10,
) -> list[tuple[str, float, dict[str, Any]]]:
    """Embed *query* and return the top-k closest chunks from Qdrant Cloud.

    Returns
    -------
    list[tuple[str, float, dict]]
        Each element is ``(chunk_text, cosine_score, payload_metadata)``.
    """
    model = _get_embedding_model()
    client = _get_client()

    query_vector: list[float] = list(model.embed([query]))[0].tolist()

    hits = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
    )

    return [
        (hit.payload.get("text", ""), hit.score, hit.payload)
        for hit in hits
    ]
