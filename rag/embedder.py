from sentence_transformers import SentenceTransformer
from rag.chunker import CodeChunk
from typing import List
import numpy as np
import structlog

logger = structlog.get_logger()

# This model runs locally — no API key needed
# Downloads once (~90MB), cached after that
MODEL_NAME = "all-MiniLM-L6-v2"

_model = None


def get_model() -> SentenceTransformer:
    """Load model once and reuse."""
    global _model
    if _model is None:
        logger.info("loading_embedding_model", model=MODEL_NAME)
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_chunks(chunks: List[CodeChunk]) -> List[dict]:
    """
    Takes list of CodeChunks and returns list of dicts
    with chunk data + embedding vector.
    """
    model = get_model()

    # Build texts to embed
    texts = []
    for chunk in chunks:
        # Combine metadata + content for richer embedding
        text = f"{chunk.chunk_type} {chunk.chunk_name} in {chunk.file_path}:\n{chunk.content}"
        texts.append(text)

    logger.info("embedding_chunks", count=len(texts))

    # Generate embeddings in batch
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True
    )

    results = []
    for chunk, embedding in zip(chunks, embeddings):
        results.append({
            "file_path":  chunk.file_path,
            "chunk_type": chunk.chunk_type,
            "chunk_name": chunk.chunk_name,
            "content":    chunk.content,
            "start_line": chunk.start_line,
            "end_line":   chunk.end_line,
            "embedding":  embedding.tolist()
        })

    logger.info("embedding_done", count=len(results))
    return results


def embed_query(query: str) -> np.ndarray:
    """
    Embeds a search query so we can compare
    it against stored chunk embeddings.
    """
    model = get_model()
    return model.encode(query, convert_to_numpy=True)
