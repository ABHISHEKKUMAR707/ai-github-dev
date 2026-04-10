from worker.celery_app import celery_app
from config.settings import settings
import structlog

logger = structlog.get_logger()


@celery_app.task(
    bind=True,
    max_retries=settings.max_retries,
    default_retry_delay=5
)
def run_agent_task(self, session_id: str, user_id: int, repo_url: str, user_intent: str):
    '''
    Main background task that runs the full AI agent.
    Called by API — runs in background via Redis/Celery.

    Steps:
    1. Update session status in MySQL
    2. Run LangGraph agent
    3. Save result back to MySQL
    4. Return PR URL on success
    '''
    try:
        logger.info(
            'agent_task_started',
            session_id=session_id,
            user_id=user_id,
            repo_url=repo_url
        )

        # Update task state so API can report progress
        self.update_state(
            state='PROGRESS',
            meta={
                'session_id': session_id,
                'status':     'starting',
                'message':    'Agent is starting...'
            }
        )

        # TODO: will be replaced with real LangGraph agent in next step
        # For now just return a placeholder
        result = {
            'session_id': session_id,
            'status':     'done',
            'message':    'Agent placeholder — LangGraph coming next',
            'pr_url':     None
        }

        logger.info('agent_task_completed', session_id=session_id)
        return result

    except Exception as exc:
        logger.error(
            'agent_task_failed',
            session_id=session_id,
            error=str(exc)
        )
        # Retry with exponential backoff
        raise self.retry(
            exc=exc,
            countdown=2 ** self.request.retries
        )
