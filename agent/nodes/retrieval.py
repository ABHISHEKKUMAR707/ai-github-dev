import os
import git
from rag.chunker import chunk_repository
from rag.indexer import build_index, load_index
from rag.retriever import hybrid_search
from agent.state import AgentState, AgentStatus
import structlog

logger = structlog.get_logger()

REPOS_DIR = "repos"


def get_repo_structure(repo_path: str) -> dict:
    """Walks repo and builds directory tree."""
    structure = {}
    skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv"}

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        rel_root = os.path.relpath(root, repo_path)
        structure[rel_root] = files

    return structure


def run(state: AgentState) -> AgentState:
    """
    Retrieval node:
    1. Clone repo
    2. Build FAISS index
    3. Search for relevant chunks using plan
    4. Pass chunks to context builder
    """
    logger.info("retrieval_started", session_id=state["session_id"])

    try:
        os.makedirs(REPOS_DIR, exist_ok=True)

        repo_url   = state["repo_url"]
        token      = state["github_token"]
        auth_url   = repo_url.replace("https://", f"https://{token}@")

        repo_name  = repo_url.rstrip("/").split("/")[-1]
        local_path = os.path.join(REPOS_DIR, f"{state['session_id']}_{repo_name}")

        # Clone repo
        if not os.path.exists(local_path):
            logger.info("cloning_repo", repo=repo_url)
            git.Repo.clone_from(auth_url, local_path)
        else:
            logger.info("repo_already_exists", path=local_path)

        # Build repo structure
        structure = get_repo_structure(local_path)

        # Build FAISS index
        repo_id = state["user_id"]
        logger.info("building_index", repo_id=repo_id)
        build_index(local_path, repo_id)

        # Search for relevant chunks using intent + plan
        search_query = state["cleaned_intent"] + " " + " ".join(state["plan"])
        chunks       = hybrid_search(search_query, repo_id, top_k=5)

        logger.info("retrieval_done", chunks=len(chunks))

        return {
            **state,
            "repo_structure":   structure,
            "retrieved_chunks": chunks,
            "status":           AgentStatus.BUILDING,
            "logs":             state["logs"] + [
                f"Repo cloned and indexed: {repo_name}",
                f"Found {len(chunks)} relevant chunks"
            ]
        }

    except Exception as e:
        logger.error("retrieval_failed", error=str(e))
        return {
            **state,
            "status":        AgentStatus.FAILED,
            "error_message": f"Retrieval failed: {str(e)}"
        }
