import os
import git
from mcp_tools.base_tool import BaseTool
from typing import Any, Dict
import structlog

logger = structlog.get_logger()

REPOS_DIR = "repos"


class RepoTool(BaseTool):
    name        = "repo_tool"
    description = "Clone, read, and write files in a GitHub repository"

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action = input_data.get("action")

        if action == "clone":
            return self._clone(input_data)
        elif action == "read":
            return self._read(input_data)
        elif action == "write":
            return self._write(input_data)
        elif action == "structure":
            return self._structure(input_data)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    def _clone(self, data: Dict) -> Dict:
        """
        Clones a GitHub repo locally.
        Input:
            repo_url:     str
            github_token: str
            session_id:   str
        """
        repo_url     = data["repo_url"]
        github_token = data["github_token"]
        session_id   = data["session_id"]

        auth_url   = repo_url.replace("https://", f"https://{github_token}@")
        repo_name  = repo_url.rstrip("/").split("/")[-1]
        local_path = os.path.join(REPOS_DIR, f"{session_id}_{repo_name}")

        os.makedirs(REPOS_DIR, exist_ok=True)

        if not os.path.exists(local_path):
            logger.info("cloning_repo", repo=repo_url)
            git.Repo.clone_from(auth_url, local_path)
        else:
            logger.info("repo_exists", path=local_path)

        return {
            "success":    True,
            "local_path": local_path,
            "repo_name":  repo_name
        }

    def _read(self, data: Dict) -> Dict:
        """
        Reads a file from local repo.
        Input:
            local_path: str
            file_path:  str
        """
        full_path = os.path.join(data["local_path"], data["file_path"])

        if not os.path.exists(full_path):
            return {"success": False, "error": f"File not found: {data['file_path']}"}

        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        return {
            "success":  True,
            "content":  content,
            "file_path": data["file_path"]
        }

    def _write(self, data: Dict) -> Dict:
        """
        Writes content to a file in local repo.
        Input:
            local_path: str
            file_path:  str
            content:    str
        Idempotent: writing same content twice is safe.
        """
        full_path = os.path.join(data["local_path"], data["file_path"])
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(data["content"])

        logger.info("file_written", path=data["file_path"])

        return {
            "success":   True,
            "file_path": data["file_path"],
            "bytes":     len(data["content"])
        }

    def _structure(self, data: Dict) -> Dict:
        """
        Returns directory tree of local repo.
        Input:
            local_path: str
        """
        local_path = data["local_path"]
        skip_dirs  = {".git", "__pycache__", "venv", "node_modules"}
        structure  = {}

        for root, dirs, files in os.walk(local_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            rel     = os.path.relpath(root, local_path)
            structure[rel] = files

        return {
            "success":   True,
            "structure": structure
        }
