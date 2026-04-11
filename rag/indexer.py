import faiss
import numpy as np
import json
import os
from rag.chunker import chunk_repository
from rag.embedder import embed_chunks
import structlog

logger = structlog.get_logger()

INDEX_DIR = "faiss_index"


def build_index(repo_path: str, repo_id: int) -> str:
    """
    Full pipeline:
    1. Chunk all Python files in repo
    2. Embed all chunks
    3. Build FAISS index
    4. Save to disk
    Returns path to saved index.
    """
    os.makedirs(INDEX_DIR, exist_ok=True)

    index_path    = os.path.join(INDEX_DIR, f"repo_{repo_id}.index")
    metadata_path = os.path.join(INDEX_DIR, f"repo_{repo_id}.json")

    # Step 1: Chunk repo
    logger.info("chunking_repo", repo_path=repo_path)
    chunks = chunk_repository(repo_path)
    logger.info("chunks_created", count=len(chunks))

    if not chunks:
        raise ValueError(f"No Python files found in {repo_path}")

    # Step 2: Embed chunks
    embedded = embed_chunks(chunks)

    # Step 3: Build FAISS index
    vectors    = np.array([e["embedding"] for e in embedded], dtype=np.float32)
    dimension  = vectors.shape[1]

    index = faiss.IndexFlatL2(dimension)
    index.add(vectors)

    # Step 4: Save index and metadata
    faiss.write_index(index, index_path)

    # Save metadata separately (FAISS only stores vectors)
    metadata = []
    for item in embedded:
        metadata.append({
            "file_path":  item["file_path"],
            "chunk_type": item["chunk_type"],
            "chunk_name": item["chunk_name"],
            "content":    item["content"],
            "start_line": item["start_line"],
            "end_line":   item["end_line"]
        })

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f)

    logger.info("index_saved", path=index_path, chunks=len(metadata))
    return index_path


def load_index(repo_id: int):
    """
    Loads FAISS index and metadata from disk.
    Returns (index, metadata_list)
    """
    index_path    = os.path.join(INDEX_DIR, f"repo_{repo_id}.index")
    metadata_path = os.path.join(INDEX_DIR, f"repo_{repo_id}.json")

    if not os.path.exists(index_path):
        raise FileNotFoundError(f"No index found for repo {repo_id}")

    index = faiss.read_index(index_path)

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    return index, metadata
