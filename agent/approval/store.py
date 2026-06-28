import redis
import json
import time
from agent.approval.models import (
    ApprovalRequest,
    ApprovalResponse,
    ApprovalStatus,
    ApprovalGate
)
from config.settings import settings

redis_client = redis.from_url(settings.redis_url)

# How long approval requests live in Redis
REQUEST_TTL  = 600   # 10 minutes
RESPONSE_TTL = 600   # 10 minutes

# How often agent checks for response (seconds)
POLL_INTERVAL = 2


def _request_key(session_id: str, gate: ApprovalGate) -> str:
    """Redis key for approval request."""
    return f"approval:request:{session_id}:{gate}"


def _response_key(session_id: str, gate: ApprovalGate) -> str:
    """Redis key for approval response."""
    return f"approval:response:{session_id}:{gate}"


def save_approval_request(request: ApprovalRequest) -> None:
    """
    Agent calls this to save an approval request.
    Frontend will read this to show UI to user.
    """
    key  = _request_key(request.session_id, request.gate)
    data = {
        "session_id":   request.session_id,
        "gate":         request.gate,
        "title":        request.title,
        "summary":      request.summary,
        "details":      request.details,
        "status":       ApprovalStatus.PENDING,
        "timeout_secs": request.timeout_secs,
        "created_at":   time.time()
    }
    redis_client.setex(key, REQUEST_TTL, json.dumps(data))


def get_approval_request(session_id: str, gate: ApprovalGate) -> dict:
    """
    Frontend calls this to get pending approval request.
    Returns None if no request exists.
    """
    key  = _request_key(session_id, gate)
    data = redis_client.get(key)
    return json.loads(data) if data else None


def save_approval_response(response: ApprovalResponse) -> None:
    """
    FastAPI saves user response here.
    Agent is waiting and will read this.
    """
    key  = _response_key(response.session_id, response.gate)
    data = {
        "session_id": response.session_id,
        "gate":       response.gate,
        "status":     response.status,
        "feedback":   response.feedback,
        "decided_at": time.time()
    }
    redis_client.setex(key, RESPONSE_TTL, json.dumps(data))


def wait_for_approval(
    session_id: str,
    gate:       ApprovalGate,
    timeout:    int = 300
) -> ApprovalResponse:
    """
    Agent calls this to BLOCK and wait for user decision.
    Polls Redis every 2 seconds until response arrives
    or timeout is reached.

    Returns ApprovalResponse with status:
    - APPROVED → continue
    - REJECTED → stop
    - MODIFIED → retry with feedback
    - EXPIRED  → timeout, auto-fail
    """
    key       = _response_key(session_id, gate)
    deadline  = time.time() + timeout
    gate_str  = gate.value if hasattr(gate, 'value') else gate

    while time.time() < deadline:
        data = redis_client.get(key)
        if data:
            parsed = json.loads(data)
            return ApprovalResponse(
                session_id=session_id,
                gate=gate,
                status=ApprovalStatus(parsed["status"]),
                feedback=parsed.get("feedback", "")
            )
        time.sleep(POLL_INTERVAL)

    # Timeout — return expired
    return ApprovalResponse(
        session_id=session_id,
        gate=gate,
        status=ApprovalStatus.EXPIRED,
        feedback="Approval timed out after 5 minutes"
    )


def clear_approval(session_id: str, gate: ApprovalGate) -> None:
    """Clean up after approval is done."""
    redis_client.delete(_request_key(session_id, gate))
    redis_client.delete(_response_key(session_id, gate))
