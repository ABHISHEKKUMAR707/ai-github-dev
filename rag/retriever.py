import numpy as np
from rank_bm25 import BM25Okapi
from rag.embedder import embed_query
from rag.indexer import load_index
from typing import List, Dict
import structlog

logger = structlog.get_logger()


def semantic_search(
    query:    str,
    index,
    metadata: List[dict],
    top_k:    int = 5
) -> List[Dict]:
    """
    Searches FAISS index using query embedding.
    Returns top_k most similar chunks.
    """
    query_vector = embed_query(query)
    query_vector = np.array([query_vector], dtype=np.float32)

    distances, indices = index.search(query_vector, top_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < len(metadata):
            chunk = metadata[idx].copy()
            chunk["score"]        = float(1 / (1 + dist))
            chunk["search_type"]  = "semantic"
            results.append(chunk)

    return results


def keyword_search(
    query:    str,
    metadata: List[dict],
    top_k:    int = 5
) -> List[Dict]:
    """
    BM25 keyword search over chunk contents.
    Good for finding exact function names or variables.
    """
    # Tokenize all chunks
    tokenized = [
        chunk["content"].lower().split()
        for chunk in metadata
    ]

    bm25   = BM25Okapi(tokenized)
    scores = bm25.get_scores(query.lower().split())

    # Get top k indices
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            chunk = metadata[idx].copy()
            chunk["score"]       = float(scores[idx])
            chunk["search_type"] = "keyword"
            results.append(chunk)

    return results


def hybrid_search(
    query:   str,
    repo_id: int,
    top_k:   int = 5
) -> List[Dict]:
    """
    Combines semantic + keyword search.
    Deduplicates and ranks by combined score.
    This is what the agent uses to find relevant code.
    """
    index, metadata = load_index(repo_id)

    semantic_results = semantic_search(query, index, metadata, top_k)
    keyword_results  = keyword_search(query, metadata, top_k)

    # Merge and deduplicate by file_path + chunk_name
    seen    = set()
    merged  = []

    for chunk in semantic_results + keyword_results:
        key = f"{chunk['file_path']}:{chunk['chunk_name']}"
        if key not in seen:
            seen.add(key)
            merged.append(chunk)

    # Sort by score descending
    merged.sort(key=lambda x: x["score"], reverse=True)

    logger.info(
        "hybrid_search_done",
        query=query,
        results=len(merged)
    )

    return merged[:top_k]
