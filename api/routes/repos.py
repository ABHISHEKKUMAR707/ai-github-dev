from fastapi import APIRouter, HTTPException, Depends
from github import Github
from db.models import User
from config.encryption import decrypt_token
from api.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/repos", tags=["repos"])


@router.get("/list")
async def list_repos(user: User = Depends(get_current_user)):
    """
    Fetches all GitHub repos for the logged in user.
    Frontend uses this to show repo selector.
    """
    try:
        github_token  = decrypt_token(user.encrypted_github_token)
        github_client = Github(github_token)
        github_user   = github_client.get_user()

        repos = []
        for repo in github_user.get_repos():
            repos.append({
                "id":             repo.id,
                "name":           repo.name,
                "full_name":      repo.full_name,
                "url":            repo.html_url,
                "clone_url":      repo.clone_url,
                "private":        repo.private,
                "default_branch": repo.default_branch,
                "description":    repo.description or ""
            })

        return {
            "username": user.github_username,
            "repos":    repos,
            "count":    len(repos)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
