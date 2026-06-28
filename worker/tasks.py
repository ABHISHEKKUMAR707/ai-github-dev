import uuid
from worker.celery_app import celery_app
from agent.graph import agent_graph
from agent.state import AgentState, AgentStatus
from agent.streaming.event_bus import publish_event
from agent.streaming.events import StreamEvent, EventType
from config.settings import settings
from db.session import SessionLocal
from db.models import Session, AgentState as AgentStateModel
import structlog

logger = structlog.get_logger()


@celery_app.task(
    bind=True,
    max_retries=settings.max_retries,
    default_retry_delay=5
)
def run_agent_task(
    self,
    session_id:   str,
    user_id:      int,
    repo_url:     str,
    user_intent:  str,
    github_token: str
):
    db = SessionLocal()

    try:
        logger.info("agent_task_started", session_id=session_id)

        publish_event(StreamEvent(
            event_type=EventType.AGENT_STARTED,
            session_id=session_id,
            message="Agent started. Initializing...",
            data={"repo_url": repo_url, "intent": user_intent}
        ))

        self.update_state(
            state="PROGRESS",
            meta={"status": "starting", "session_id": session_id}
        )

        initial_state = AgentState(
            session_id=session_id,
            user_id=user_id,
            repo_url=repo_url,
            github_token=github_token,
            raw_input=user_intent,
            cleaned_intent=user_intent,
            plan=[],
            current_step=0,
            retrieved_chunks=[],
            repo_structure={},
            assembled_context="",
            file_changes=[],
            validation_result=None,
            retry_count=0,
            max_retries=settings.max_retries,
            branch_name=None,
            pr_url=None,
            status=AgentStatus.PLANNING,
            error_message=None,
            logs=[]
        )

        final_state = agent_graph.invoke(initial_state)

        db_session = db.query(Session).filter(
            Session.session_id == session_id
        ).first()

        if db_session:
            db_session.status        = final_state["status"]
            db_session.pr_url        = final_state.get("pr_url")
            db_session.error_message = final_state.get("error_message")
            db.commit()

        state_record = AgentStateModel(
            session_id=session_id,
            state_data=dict(final_state),
            current_node="done",
            retry_count=final_state["retry_count"]
        )
        db.add(state_record)
        db.commit()

        logger.info(
            "agent_task_completed",
            session_id=session_id,
            status=final_state["status"],
            pr_url=final_state.get("pr_url")
        )

        return {
            "session_id": session_id,
            "status":     final_state["status"],
            "pr_url":     final_state.get("pr_url"),
            "logs":       final_state.get("logs", [])
        }

    except Exception as exc:
        logger.error("agent_task_failed", session_id=session_id, error=str(exc))

        publish_event(StreamEvent(
            event_type=EventType.AGENT_FAILED,
            session_id=session_id,
            message=f"Agent task failed: {str(exc)}",
            data={"error": str(exc)}
        ))

        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

    finally:
        db.close()
