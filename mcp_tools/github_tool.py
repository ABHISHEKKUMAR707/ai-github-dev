from github import Github
from mcp_tools.base_tool import BaseTool
from typing import Any, Dict
import git
import os
import structlog

logger = structlog.get_logger()

REPOS_DIR = "repos"


class GithubTool(BaseTool):
    name        = "github_tool"
    description = "Create branches, commit files, and open PRs on GitHub"

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action = input_data.get("action")

        if action == "create_branch":
            return self._create_branch(input_data)
        elif action == "commit_files":
            return self._commit_files(input_data)
        elif action == "create_pr":
            return self._create_pr(input_data)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    def _create_branch(self, data: Dict) -> Dict:
        """
        Creates new branch in local repo.
        Input:
            local_path:  str
            branch_name: str
        """
        local_repo  = git.Repo(data["local_path"])
        branch_name = data["branch_name"]

        local_repo.git.checkout("-b", branch_name)
        logger.info("branch_created", branch=branch_name)

        return {
            "success":     True,
            "branch_name": branch_name
        }

    def _commit_files(self, data: Dict) -> Dict:
        """
        Stages and commits all changes.
        Input:
            local_path:     str
            commit_message: str
            github_token:   str
            branch_name:    str
        """
        local_repo = git.Repo(data["local_path"])

        # Stage all changes
        local_repo.git.add("--all")

        # Commit
        local_repo.index.commit(data["commit_message"])

        # Push to GitHub
        origin = local_repo.remote("origin")
        origin.push(data["branch_name"])

        logger.info("committed_and_pushed", branch=data["branch_name"])

        return {
            "success":     True,
            "branch_name": data["branch_name"],
            "message":     data["commit_message"]
        }

    def _create_pr(self, data: Dict) -> Dict:
        """
        Opens a Pull Request on GitHub.
        Input:
            github_token: str
            repo_url:     str
            branch_name:  str
            title:        str
            body:         str
        """
        github_client = Github(data["github_token"])
        repo_full     = data["repo_url"].replace("https://github.com/", "")
        github_repo   = github_client.get_repo(repo_full)

        pr = github_repo.create_pull(
            title=data["title"],
            body=data["body"],
            head=data["branch_name"],
            base=github_repo.default_branch
        )

        logger.info("pr_created", url=pr.html_url)

        return {
            "success":  True,
            "pr_url":   pr.html_url,
            "pr_number": pr.number
        }
