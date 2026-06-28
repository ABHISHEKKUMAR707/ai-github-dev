import re
from agent.state import AgentState, AgentStatus, FileChange
from agent.streaming.event_bus import publish_event
from agent.streaming.events import StreamEvent, EventType
from agent.approval.manager import request_approval, is_approved, is_rejected, is_modified
from agent.approval.models import ApprovalGate
from config.claude_client import call_claude
import structlog

logger = structlog.get_logger()

CODE_GEN_SYSTEM_PROMPT = """
You are a senior software engineer writing production-quality code.

When given a repository context and implementation plan, you must:
1. Write complete, working code for each file
2. Follow existing code style in the repository
3. Never leave placeholder comments like "add code here"
4. Always include proper imports
5. Handle edge cases and errors

Output format — you MUST follow this exactly:
For each file you create or modify, output:

FILE: path/to/file.py
ACTION: create
```python
# full file content here
```

FILE: path/to/existing.py
ACTION: modify
```python
# full updated file content here
```

Only output file blocks. No explanations outside the blocks.
"""


def parse_file_changes(response: str) -> list:
    """Parses Claude response into list of FileChange objects."""
    changes = []
    parts   = response.split("FILE:")

    for part in parts[1:]:
        try:
            lines      = part.strip().split("\n")
            file_path  = lines[0].strip()
            action_line = lines[1].strip() if len(lines) > 1 else ""
            action      = "create"
            if "ACTION:" in action_line:
                action = action_line.replace("ACTION:", "").strip().lower()

            code_match = re.search(
                r"```(?:python|javascript|typescript|)?\n(.*?)```",
                part, re.DOTALL
            )
            if code_match:
                content = code_match.group(1).strip()
                changes.append(FileChange(
                    file_path=file_path,
                    original_content="",
                    new_content=content,
                    change_type=action
                ))
        except Exception:
            continue
    return changes


def generate_code(state: AgentState, feedback: str = "") -> list:
    """Calls Claude to generate code."""
    feedback_section = f"\nUser feedback to incorporate: {feedback}" if feedback else ""

    prompt = f"""
Here is the repository context and what needs to be implemented:

{state["assembled_context"]}
{feedback_section}

Now implement all the steps in the plan.
Generate complete, production-ready code for each file.
"""
    response     = call_claude(prompt=prompt, system=CODE_GEN_SYSTEM_PROMPT, max_tokens=8000)
    file_changes = parse_file_changes(response)

    if not file_changes:
        raise ValueError("Claude returned no file changes")

    return file_changes


def run(state: AgentState) -> AgentState:
    """
    Code Generator node with Gate 2 approval.

    Flow:
    1. Claude generates code
    2. Show generated files to user → wait for approval
    3. If approved  → continue to validator
    4. If rejected  → stop
    5. If modified  → regenerate with feedback
    """
    logger.info("code_generator_started", session_id=state["session_id"])

    publish_event(StreamEvent(
        event_type=EventType.CODEGEN_STARTED,
        session_id=state["session_id"],
        message="Generating code with Claude AI...",
        data={"retry": state["retry_count"]}
    ))

    feedback    = ""
    max_retries = 3

    for attempt in range(max_retries):
        try:
            # Step 1: Generate code
            file_changes = generate_code(state, feedback)

            publish_event(StreamEvent(
                event_type=EventType.CODEGEN_COMPLETED,
                session_id=state["session_id"],
                message=f"Generated {len(file_changes)} file changes",
                data={"files": [c["file_path"] for c in file_changes]}
            ))

            # Build file summary for approval UI
            file_summary = []
            for change in file_changes:
                line_count = len(change["new_content"].splitlines())
                file_summary.append({
                    "file":       change["file_path"],
                    "action":     change["change_type"],
                    "lines":      line_count,
                    "preview":    change["new_content"][:200] + "..."
                                  if len(change["new_content"]) > 200
                                  else change["new_content"]
                })

            # Step 2: Request code approval
            response = request_approval(
                session_id=state["session_id"],
                gate=ApprovalGate.CODE,
                title="Review Generated Code",
                summary=f"Claude generated {len(file_changes)} files. Review before committing.",
                details={
                    "files":   file_summary,
                    "total":   len(file_changes)
                }
            )

            # Step 3: Handle decision
            if is_approved(response):
                logger.info("code_approved", files=len(file_changes))
                return {
                    **state,
                    "file_changes": file_changes,
                    "status":       AgentStatus.VALIDATING,
                    "logs":         state["logs"] + [f"Code approved: {len(file_changes)} files"]
                }

            elif is_modified(response):
                feedback = response.feedback
                logger.info("code_modification_requested", feedback=feedback)
                publish_event(StreamEvent(
                    event_type=EventType.CODEGEN_STARTED,
                    session_id=state["session_id"],
                    message=f"Regenerating with feedback: {feedback}",
                    data={"feedback": feedback}
                ))
                continue

            else:
                logger.info("code_rejected", session_id=state["session_id"])
                return {
                    **state,
                    "status":        AgentStatus.FAILED,
                    "error_message": f"Code rejected by user: {response.feedback}"
                }

        except Exception as e:
            logger.error("code_generator_failed", error=str(e))
            return {
                **state,
                "status":        AgentStatus.FAILED,
                "error_message": f"Code generation failed: {str(e)}"
            }

    return {
        **state,
        "status":        AgentStatus.FAILED,
        "error_message": "Code could not be approved after 3 attempts"
    }
