from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class EventType(str, Enum):
    # Agent lifecycle
    AGENT_STARTED    = "agent_started"
    AGENT_COMPLETED  = "agent_completed"
    AGENT_FAILED     = "agent_failed"

    # Node events
    PLANNER_STARTED      = "planner_started"
    PLANNER_COMPLETED    = "planner_completed"
    RETRIEVAL_STARTED    = "retrieval_started"
    RETRIEVAL_CLONING    = "retrieval_cloning"
    RETRIEVAL_INDEXING   = "retrieval_indexing"
    RETRIEVAL_SEARCHING  = "retrieval_searching"
    RETRIEVAL_COMPLETED  = "retrieval_completed"
    CONTEXT_STARTED      = "context_started"
    CONTEXT_COMPLETED    = "context_completed"
    CODEGEN_STARTED      = "codegen_started"
    CODEGEN_COMPLETED    = "codegen_completed"
    VALIDATOR_STARTED    = "validator_started"
    VALIDATOR_COMPLETED  = "validator_completed"
    DECISION_RETRY       = "decision_retry"
    DECISION_COMMIT      = "decision_commit"
    DECISION_FAILED      = "decision_failed"
    COMMIT_STARTED       = "commit_started"
    COMMIT_WRITING       = "commit_writing"
    COMMIT_PUSHING       = "commit_pushing"
    PR_CREATED           = "pr_created"


@dataclass
class StreamEvent:
    """
    Single streaming event sent to client.
    Every node creates these and publishes to Redis.
    """
    event_type:  str
    session_id:  str
    message:     str
    data:        Dict[str, Any] = field(default_factory=dict)

    def to_sse(self) -> str:
        """
        Formats event as SSE string.
        Browser EventSource reads this format.
        """
        import json
        payload = {
            "event_type": self.event_type,
            "session_id": self.session_id,
            "message":    self.message,
            "data":       self.data
        }
        return f"data: {json.dumps(payload)}\n\n"
