import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from worker.tasks import run_agent_task
from db.session import get_db
from db.models import Session as SessionModel, User, Repository
from config.encryption import decrypt_token
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix='/agent', tags=['agent'])


class AgentRequest(BaseModel):
    repo_url:    str    # e.g. https://github.com/user/repo
    user_intent: str    # e.g. Add attendance tracker feature


class AgentResponse(BaseModel):
    session_id: str
    task_id:    str
    message:    str


@router.post('/run', response_model=AgentResponse)
async def run_agent(
    request: AgentRequest,
    db:      Session = Depends(get_db)
):
    '''
    Triggers the AI agent to modify a GitHub repository.
    1. Validates user and repo
    2. Creates session in MySQL
    3. Queues Celery task
    4. Returns task_id for progress tracking
    '''
    try:
        # TODO: get user from JWT token
        # For now using first user for testing
        user = db.query(User).first()
        if not user:
            raise HTTPException(
                status_code=401,
                detail='No user found. Please login first.'
            )

        # Decrypt GitHub token for agent use
        github_token = decrypt_token(user.encrypted_github_token)

        # Create session record
        session_id = str(uuid.uuid4())
        db_session = SessionModel(
            session_id=session_id,
            user_id=user.id,
            raw_input=request.user_intent,
            cleaned_intent=request.user_intent
        )
        db.add(db_session)
        db.commit()

        # Queue background task
        task = run_agent_task.delay(
            session_id=session_id,
            user_id=user.id,
            repo_url=request.repo_url,
            user_intent=request.user_intent,
            github_token=github_token
        )

        logger.info(
            'agent_triggered',
            session_id=session_id,
            task_id=task.id,
            repo=request.repo_url
        )

        return AgentResponse(
            session_id=session_id,
            task_id=task.id,
            message='Agent started. Use task_id to track progress.'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error('agent_trigger_failed', error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/status/{task_id}')
async def get_status(task_id: str):
    '''
    Check progress of a running agent task.
    Returns current status and PR URL when done.
    '''
    from worker.celery_app import celery_app
    task = celery_app.AsyncResult(task_id)

    if task.state == 'PENDING':
        return {'status': 'pending', 'message': 'Task is waiting to start'}

    if task.state == 'PROGRESS':
        return {'status': 'running', 'info': task.info}

    if task.state == 'SUCCESS':
        return {'status': 'done', 'result': task.result}

    if task.state == 'FAILURE':
        return {'status': 'failed', 'error': str(task.info)}

    return {'status': task.state}
