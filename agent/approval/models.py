from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class ApprovalStatus(str, Enum):
    """
    Possible states of an approval request.
    PENDING  = waiting for user decision
    APPROVED = user said yes
    REJECTED = user said no
    MODIFIED = user requested changes
    EXPIRED  = user took too long (timeout)
    """
    PENDING  = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    EXPIRED  = "expired"


class ApprovalGate(str, Enum):
    """
    The 3 gates where agent pauses for approval.
    PLAN   = after planner creates steps
    CODE   = after code generator writes code
    COMMIT = before pushing to GitHub
    """
    PLAN   = "plan"
    CODE   = "code"
    COMMIT = "commit"


@dataclass
class ApprovalRequest:
    """
    What the agent sends to the frontend
    when it needs human approval.

    Example for PLAN gate:
        gate       = "plan"
        title      = "Review Implementation Plan"
        summary    = "I will modify 3 files"
        details    = {"steps": ["Create x.py", "Modify app.py"]}
        session_id = "abc-123"
    """
    session_id:  str
    gate:        ApprovalGate
    title:       str
    summary:     str
    details:     Dict[str, Any] = field(default_factory=dict)
    timeout_secs: int = 300    # 5 minutes to respond


@dataclass
class ApprovalResponse:
    """
    What the user sends back when they
    approve, reject, or request changes.

    Example:
        status   = "approved"
        feedback = ""            (empty = no changes needed)

    Example with changes:
        status   = "modified"
        feedback = "Use snake_case for function names"
    """
    session_id: str
    gate:       ApprovalGate
    status:     ApprovalStatus
    feedback:   str = ""        # only used when status = modified
