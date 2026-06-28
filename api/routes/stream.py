from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from jose import jwt, JWTError
from config.settings import settings
from db.session import get_db
from db.models import User
from sqlalchemy.orm import Session
from agent.streaming.event_bus import subscribe_to_session
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/agent", tags=["streaming"])


def get_user_from_token(token: str, db: Session) -> User:
    """Validates JWT from query param for SSE connections."""
    try:
        payload = jwt.decode(token, settings.app_secret_key, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/stream/{session_id}")
async def stream_events(
    session_id: str,
    token:      str = Query(...),
    db:         Session = Depends(get_db)
):
    """
    SSE endpoint for real time agent progress.
    Token passed as query param because EventSource
    cannot send Authorization headers.
    """
    user = get_user_from_token(token, db)
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
