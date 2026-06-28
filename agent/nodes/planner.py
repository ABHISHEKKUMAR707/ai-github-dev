from agent.state import AgentState, AgentStatus
from agent.streaming.event_bus import publish_event
from agent.streaming.events import StreamEvent, EventType
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


def run(state: AgentState) -> AgentState:
    logger.info("planner_started", session_id=state["session_id"])

    # Publish start event
    publish_event(StreamEvent(
        event_type=EventType.PLANNER_STARTED,
        session_id=state["session_id"],
        message="Planning your request...",
        data={"intent": state["cleaned_intent"]}
    ))

    try:
        prompt = f"""
Repository: {state["repo_url"]}
Developer request: {state["cleaned_intent"]}
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

        # Publish completion event
        publish_event(StreamEvent(
            event_type=EventType.PLANNER_COMPLETED,
            session_id=state["session_id"],
            message=f"Plan created with {len(plan)} steps",
            data={"steps": plan}
        ))

        logger.info("planner_done", steps=len(plan))

        return {
            **state,
            "plan":         plan,
            "current_step": 0,
            "status":       AgentStatus.RETRIEVING,
            "logs":         state["logs"] + [f"Plan created with {len(plan)} steps"]
        }

    except Exception as e:
        logger.error("planner_failed", error=str(e))

        publish_event(StreamEvent(
            event_type=EventType.AGENT_FAILED,
            session_id=state["session_id"],
            message=f"Planning failed: {str(e)}",
            data={"error": str(e)}
        ))

        return {
            **state,
            "status":        AgentStatus.FAILED,
            "error_message": f"Planner failed: {str(e)}"
        }
