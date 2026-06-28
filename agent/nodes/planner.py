from agent.state import AgentState, AgentStatus
from agent.streaming.event_bus import publish_event
from agent.streaming.events import StreamEvent, EventType
from agent.approval.manager import request_approval, is_approved, is_rejected, is_modified
from agent.approval.models import ApprovalGate
from config.claude_client import call_claude
import structlog

logger = structlog.get_logger()

PLANNER_SYSTEM_PROMPT = """
You are a senior software engineer.
Your job is to analyze a developer request and break it into
clear, specific implementation steps.

Rules:
- Each step must be a single file action
- Be specific about file names and what changes
- Maximum 6 steps
- Output ONLY a numbered list, nothing else

Example output:
1. Create attendance/tracker.py with AttendanceTracker class
2. Create attendance/__init__.py to export AttendanceTracker
3. Modify app.py to import and register attendance routes
4. Modify requirements.txt to add any new dependencies
"""


def create_plan(intent: str, repo_url: str, feedback: str = "") -> list:
    """Calls Claude to create implementation plan."""
    feedback_section = f"\nPrevious feedback to incorporate: {feedback}" if feedback else ""

    prompt = f"""
Repository: {repo_url}
Developer request: {intent}
{feedback_section}
Break this into specific implementation steps.
"""
    response = call_claude(
        prompt=prompt,
        system=PLANNER_SYSTEM_PROMPT,
        max_tokens=500
    )

    lines = response.strip().split("\n")
    plan  = []
    for line in lines:
        line = line.strip()
        if line and line[0].isdigit():
            step = line.split(".", 1)[-1].strip()
            plan.append(step)
    return plan


def run(state: AgentState) -> AgentState:
    """
    Planner node with Gate 1 approval.

    Flow:
    1. Claude creates plan
    2. Show plan to user → wait for approval
    3. If approved  → continue
    4. If rejected  → stop
    5. If modified  → replan with feedback
    """
    logger.info("planner_started", session_id=state["session_id"])

    publish_event(StreamEvent(
        event_type=EventType.PLANNER_STARTED,
        session_id=state["session_id"],
        message="Planning your request...",
        data={"intent": state["cleaned_intent"]}
    ))

    feedback    = ""
    max_retries = 3

    for attempt in range(max_retries):
        try:
            # Step 1: Create plan
            plan = create_plan(
                state["cleaned_intent"],
                state["repo_url"],
                feedback
            )

            publish_event(StreamEvent(
                event_type=EventType.PLANNER_COMPLETED,
                session_id=state["session_id"],
                message=f"Plan created with {len(plan)} steps",
                data={"steps": plan, "attempt": attempt + 1}
            ))

            # Step 2: Request plan approval
            response = request_approval(
                session_id=state["session_id"],
                gate=ApprovalGate.PLAN,
                title="Review Implementation Plan",
                summary=f"I will make {len(plan)} changes to your repository",
                details={
                    "steps":   plan,
                    "repo":    state["repo_url"],
                    "intent":  state["cleaned_intent"]
                }
            )

            # Step 3: Handle decision
            if is_approved(response):
                logger.info("plan_approved", session_id=state["session_id"])
                return {
                    **state,
                    "plan":         plan,
                    "current_step": 0,
                    "status":       AgentStatus.RETRIEVING,
                    "logs":         state["logs"] + [f"Plan approved: {len(plan)} steps"]
                }

            elif is_modified(response):
                feedback = response.feedback
                logger.info("plan_modified", feedback=feedback)
                publish_event(StreamEvent(
                    event_type=EventType.PLANNER_STARTED,
                    session_id=state["session_id"],
                    message=f"Replanning with feedback: {feedback}",
                    data={"feedback": feedback}
                ))
                continue   # retry with feedback

            else:
                # Rejected or expired
                logger.info("plan_rejected", session_id=state["session_id"])
                return {
                    **state,
                    "status":        AgentStatus.FAILED,
                    "error_message": f"Plan rejected by user: {response.feedback}"
                }

        except Exception as e:
            logger.error("planner_failed", error=str(e))
            return {
                **state,
                "status":        AgentStatus.FAILED,
                "error_message": f"Planner failed: {str(e)}"
            }

    return {
        **state,
        "status":        AgentStatus.FAILED,
        "error_message": "Plan could not be approved after 3 attempts"
    }
