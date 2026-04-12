from mcp_tools.base_tool import BaseTool
from rag.indexer import build_index, load_index
from rag.retriever import hybrid_search
from typing import Any, Dict
import structlog

logger = structlog.get_logger()


class RAGTool(BaseTool):
    name        = "rag_tool"
    description = "Index a repository and search for relevant code chunks"

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action = input_data.get("action")

        if action == "index":
            return self._index(input_data)
        elif action == "search":
            return self._search(input_data)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    def _index(self, data: Dict) -> Dict:
        """
        Builds FAISS index for a repository.
        Input:
            repo_path: str
            repo_id:   int
        """
        repo_path = data["repo_path"]
        repo_id   = data["repo_id"]

        logger.info("indexing_repo", repo_path=repo_path)
        index_path = build_index(repo_path, repo_id)

        return {
            "success":    True,
            "index_path": index_path,
            "repo_id":    repo_id
        }

    def _search(self, data: Dict) -> Dict:
        """
        Searches indexed repo for relevant chunks.
        Input:
            query:   str
            repo_id: int
            top_k:   int (optional, default 5)
        """
        query   = data["query"]
        repo_id = data["repo_id"]
        top_k   = data.get("top_k", 5)

        logger.info("searching_repo", query=query, repo_id=repo_id)
        chunks = hybrid_search(query, repo_id, top_k=top_k)

        return {
            "success": True,
            "chunks":  chunks,
            "count":   len(chunks)
        }
