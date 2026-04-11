import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from worker.tasks import run_agent_task
from db.session import get_db
from db.models import Session as SessionModel, User
from config.encryption import decrypt_token
from api.middleware.auth_middleware import get_current_user
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentRequest(BaseModel):
    repo_url:    str
    user_intent: str


class AgentResponse(BaseModel):
    session_id: str
    task_id:    str
    message:    str


@router.post("/run", response_model=AgentResponse)
async def run_agent(
    request: AgentRequest,
    db:      Session = Depends(get_db),
    user:    User    = Depends(get_current_user)
):
    """
    Triggers the AI agent — requires JWT token.
    """
    try:
        github_token = decrypt_token(user.encrypted_github_token)

        session_id = str(uuid.uuid4())
        db_session = SessionModel(
            session_id=session_id,
            user_id=user.id,
            raw_input=request.user_intent,
            cleaned_intent=request.user_intent
        )
        db.add(db_session)
        db.commit()

        task = run_agent_task.delay(
            session_id=session_id,
            user_id=user.id,
            repo_url=request.repo_url,
            user_intent=request.user_intent,
            github_token=github_token
        )

        logger.info(
            "agent_triggered",
            session_id=session_id,
            user=user.github_username,
            repo=request.repo_url
        )

        return AgentResponse(
            session_id=session_id,
            task_id=task.id,
            message="Agent started. Use task_id to track progress."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("agent_trigger_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}")
async def get_status(
    task_id: str,
    user:    User = Depends(get_current_user)
):
    """Check progress of agent task."""
    from worker.celery_app import celery_app
    task = celery_app.AsyncResult(task_id)

    if task.state == "PENDING":
        return {"status": "pending", "message": "Task is waiting to start"}
    if task.state == "PROGRESS":
        return {"status": "running", "info": task.info}
    if task.state == "SUCCESS":
        return {"status": "done", "result": task.result}
    if task.state == "FAILURE":
        return {"status": "failed", "error": str(task.info)}

    return {"status": task.state}
