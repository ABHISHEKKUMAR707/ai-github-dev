from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from db.models import User
from api.middleware.auth_middleware import get_current_user
from agent.streaming.event_bus import subscribe_to_session
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/agent", tags=["streaming"])


@router.get("/stream/{session_id}")
async def stream_events(
    session_id: str,
    user: User = Depends(get_current_user)
):
    """
    SSE endpoint — browser connects here after /agent/run.
    Streams real-time events from Redis until agent completes.

    Frontend usage:
        const es = new EventSource('/agent/stream/SESSION_ID?token=JWT')
        es.onmessage = (e) => { const data = JSON.parse(e.data) }
    """
    logger.info("stream_connected", session_id=session_id, user=user.github_username)

    def event_generator():
        try:
            for event in subscribe_to_session(session_id):
                yield event
        except GeneratorExit:
            logger.info("stream_disconnected", session_id=session_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":               "no-cache",
            "X-Accel-Buffering":           "no",
            "Access-Control-Allow-Origin": "*"
        }
    )
