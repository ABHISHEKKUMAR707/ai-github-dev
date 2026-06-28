import os
import git
from rag.chunker import chunk_repository
from rag.indexer import build_index
from rag.retriever import hybrid_search
from agent.state import AgentState, AgentStatus
from agent.streaming.event_bus import publish_event
from agent.streaming.events import StreamEvent, EventType
import structlog

logger = structlog.get_logger()

REPOS_DIR = "repos"


def get_repo_structure(repo_path: str) -> dict:
    structure = {}
    skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv"}
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        rel_root = os.path.relpath(root, repo_path)
        structure[rel_root] = files
    return structure


def run(state: AgentState) -> AgentState:
    logger.info("retrieval_started", session_id=state["session_id"])

    publish_event(StreamEvent(
        event_type=EventType.RETRIEVAL_STARTED,
        session_id=state["session_id"],
        message="Starting repository retrieval...",
        data={}
    ))

    try:
        os.makedirs(REPOS_DIR, exist_ok=True)

        repo_url   = state["repo_url"]
        token      = state["github_token"]
        auth_url   = repo_url.replace("https://", f"https://{token}@")
        repo_name  = repo_url.rstrip("/").split("/")[-1]
        local_path = os.path.join(REPOS_DIR, f"{state['session_id']}_{repo_name}")

        if not os.path.exists(local_path):
            publish_event(StreamEvent(
                event_type=EventType.RETRIEVAL_CLONING,
                session_id=state["session_id"],
                message=f"Cloning repository {repo_name}...",
                data={"repo": repo_url}
            ))
            git.Repo.clone_from(auth_url, local_path)
        else:
            logger.info("repo_exists", path=local_path)

        structure = get_repo_structure(local_path)

        publish_event(StreamEvent(
            event_type=EventType.RETRIEVAL_INDEXING,
            session_id=state["session_id"],
            message="Indexing repository with RAG...",
            data={}
        ))

        repo_id = state["user_id"]
        build_index(local_path, repo_id)

        publish_event(StreamEvent(
            event_type=EventType.RETRIEVAL_SEARCHING,
            session_id=state["session_id"],
            message="Searching for relevant code chunks...",
            data={}
        ))

        search_query = state["cleaned_intent"] + " " + " ".join(state["plan"])
        chunks       = hybrid_search(search_query, repo_id, top_k=5)

        publish_event(StreamEvent(
            event_type=EventType.RETRIEVAL_COMPLETED,
            session_id=state["session_id"],
            message=f"Found {len(chunks)} relevant code chunks",
            data={"chunks": len(chunks)}
        ))

        logger.info("retrieval_done", chunks=len(chunks))

        return {
            **state,
            "repo_structure":   structure,
            "retrieved_chunks": chunks,
            "status":           AgentStatus.BUILDING,
            "logs":             state["logs"] + [f"Found {len(chunks)} relevant chunks"]
        }

    except Exception as e:
        logger.error("retrieval_failed", error=str(e))

        publish_event(StreamEvent(
            event_type=EventType.AGENT_FAILED,
            session_id=state["session_id"],
            message=f"Retrieval failed: {str(e)}",
            data={"error": str(e)}
        ))

        return {
            **state,
            "status":        AgentStatus.FAILED,
            "error_message": f"Retrieval failed: {str(e)}"
        }
