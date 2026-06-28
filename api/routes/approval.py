from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from db.models import User
from api.middleware.auth_middleware import get_current_user
from agent.approval.store import (
    get_approval_request,
    save_approval_response
)
from agent.approval.models import (
    ApprovalResponse,
    ApprovalStatus,
    ApprovalGate
)
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/approval", tags=["approval"])


class ApprovalDecision(BaseModel):
    """
    Body sent by frontend when user
    approves, rejects, or requests changes.
    """
    status:   str    # approved / rejected / modified
    feedback: str = ""  # only needed when status = modified


@router.get("/{session_id}/{gate}")
async def get_pending_approval(
    session_id: str,
    gate:       str,
    user:       User = Depends(get_current_user)
):
    """
    Frontend calls this to get the current
    pending approval request for a gate.

    Returns the title, summary, and details
    the agent wants the user to review.
    """
    try:
        approval_gate = ApprovalGate(gate)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid gate: {gate}. Must be: plan, code, commit"
        )

    request = get_approval_request(session_id, approval_gate)

    if not request:
        raise HTTPException(
            status_code=404,
            detail=f"No pending approval for gate: {gate}"
        )

    return {
        "session_id": session_id,
        "gate":       gate,
        "title":      request["title"],
        "summary":    request["summary"],
        "details":    request["details"],
        "status":     request["status"],
        "timeout":    request["timeout_secs"]
    }


@router.post("/{session_id}/{gate}/respond")
async def respond_to_approval(
    session_id: str,
    gate:       str,
    decision:   ApprovalDecision,
    user:       User = Depends(get_current_user)
):
    """
    Frontend calls this when user clicks
    Approve / Reject / Request Changes.

    This unblocks the waiting agent node.
    """
    try:
        approval_gate   = ApprovalGate(gate)
        approval_status = ApprovalStatus(decision.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    response = ApprovalResponse(
        session_id=session_id,
        gate=approval_gate,
        status=approval_status,
        feedback=decision.feedback
    )

    save_approval_response(response)

    logger.info(
        "approval_responded",
        session_id=session_id,
        gate=gate,
        status=decision.status,
        user=user.github_username
    )

    return {
        "session_id": session_id,
        "gate":       gate,
        "status":     decision.status,
        "message":    f"Decision '{decision.status}' saved. Agent will continue."
    }


@router.get("/{session_id}/pending")
async def get_pending_gates(
    session_id: str,
    user:       User = Depends(get_current_user)
):
    """
    Check which gates are currently
    waiting for approval.

    Frontend polls this to know if
    any gate needs attention.
    """
    pending = []
    for gate in ApprovalGate:
        request = get_approval_request(session_id, gate)
        if request and request["status"] == "pending":
            pending.append({
                "gate":    gate.value,
                "title":   request["title"],
                "summary": request["summary"]
            })

    return {
        "session_id":    session_id,
        "pending_gates": pending,
        "has_pending":   len(pending) > 0
    }
