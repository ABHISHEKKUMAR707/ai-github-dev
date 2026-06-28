from agent.approval.models import (
    ApprovalRequest,
    ApprovalResponse,
    ApprovalStatus,
    ApprovalGate
)
from agent.approval.store import (
    save_approval_request,
    wait_for_approval,
    clear_approval
)
from agent.streaming.event_bus import publish_event
from agent.streaming.events import StreamEvent
import structlog

logger = structlog.get_logger()

# Custom event types for approval
APPROVAL_NEEDED   = "approval_needed"
APPROVAL_RECEIVED = "approval_received"


def request_approval(
    session_id: str,
    gate:       ApprovalGate,
    title:      str,
    summary:    str,
    details:    dict,
    timeout:    int = 300
) -> ApprovalResponse:
    """
    Main function called by agent nodes.

    Full cycle:
    1. Save approval request to Redis
    2. Publish SSE event → frontend shows approval UI
    3. Wait for user response (blocks until response or timeout)
    4. Publish SSE event → frontend shows decision
    5. Return response to agent node

    Agent node then decides:
    - APPROVED  → continue to next step
    - REJECTED  → stop and report to user
    - MODIFIED  → retry with user feedback
    - EXPIRED   → timeout, fail gracefully
    """
    logger.info(
        "approval_requested",
        session_id=session_id,
        gate=gate,
        title=title
    )

    # Step 1: Save to Redis
    request = ApprovalRequest(
        session_id=session_id,
        gate=gate,
        title=title,
        summary=summary,
        details=details,
        timeout_secs=timeout
    )
    save_approval_request(request)

    # Step 2: Notify frontend via SSE
    publish_event(StreamEvent(
        event_type=APPROVAL_NEEDED,
        session_id=session_id,
        message=f"Waiting for your approval: {title}",
        data={
            "gate":    gate,
            "title":   title,
            "summary": summary,
            "details": details,
            "timeout": timeout
        }
    ))

    # Step 3: Wait for response (blocks here)
    logger.info("waiting_for_approval", session_id=session_id, gate=gate)
    response = wait_for_approval(session_id, gate, timeout)

    # Step 4: Notify frontend of decision
    publish_event(StreamEvent(
        event_type=APPROVAL_RECEIVED,
        session_id=session_id,
        message=f"Approval {response.status}: {gate}",
        data={
            "gate":     gate,
            "status":   response.status,
            "feedback": response.feedback
        }
    ))

    # Step 5: Cleanup Redis keys
    clear_approval(session_id, gate)

    logger.info(
        "approval_received",
        session_id=session_id,
        gate=gate,
        status=response.status
    )

    return response


def is_approved(response: ApprovalResponse) -> bool:
    """Helper — returns True only if user approved."""
    return response.status == ApprovalStatus.APPROVED


def is_rejected(response: ApprovalResponse) -> bool:
    """Helper — returns True if user rejected or timed out."""
    return response.status in [
        ApprovalStatus.REJECTED,
        ApprovalStatus.EXPIRED
    ]


def is_modified(response: ApprovalResponse) -> bool:
    """Helper — returns True if user wants changes."""
    return response.status == ApprovalStatus.MODIFIED
