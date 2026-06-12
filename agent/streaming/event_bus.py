import redis
import json
from agent.streaming.events import StreamEvent
from config.settings import settings

redis_client = redis.from_url(settings.redis_url)


def get_channel(session_id: str) -> str:
    """Each session has its own Redis channel."""
    return f"stream:{session_id}"


def publish_event(event: StreamEvent) -> None:
    """
    Called by agent nodes to publish events.
    Runs inside Celery worker process.
    """
    channel = get_channel(event.session_id)
    redis_client.publish(channel, json.dumps({
        "event_type": event.event_type,
        "session_id": event.session_id,
        "message":    event.message,
        "data":       event.data
    }))


def subscribe_to_session(session_id: str):
    """
    Called by SSE endpoint to listen for events.
    Runs inside FastAPI process.
    Returns a generator that yields SSE strings.
    """
    pubsub  = redis_client.pubsub()
    channel = get_channel(session_id)
    pubsub.subscribe(channel)

    try:
        for message in pubsub.listen():
            if message["type"] == "message":
                data    = json.loads(message["data"])
                payload = json.dumps(data)
                yield f"data: {payload}\n\n"

                # Stop listening when agent is done
                if data["event_type"] in [
                    "agent_completed",
                    "agent_failed"
                ]:
                    break
    finally:
        pubsub.unsubscribe(channel)
        pubsub.close()
