import ast
from agent.state import AgentState, AgentStatus, ValidationResult
from agent.streaming.event_bus import publish_event
from agent.streaming.events import StreamEvent, EventType
import structlog

logger = structlog.get_logger()


def validate_python_syntax(code: str, file_path: str) -> list:
    errors = []
    try:
        ast.parse(code)
    except SyntaxError as e:
        errors.append(f"{file_path}: SyntaxError at line {e.lineno}: {e.msg}")
    except Exception as e:
        errors.append(f"{file_path}: Parse error: {str(e)}")
    return errors


def run(state: AgentState) -> AgentState:
    logger.info("validator_started", session_id=state["session_id"])

    publish_event(StreamEvent(
        event_type=EventType.VALIDATOR_STARTED,
        session_id=state["session_id"],
        message="Validating generated code...",
        data={"files": len(state["file_changes"])}
    ))

    try:
        all_errors   = []
        all_warnings = []

        for change in state["file_changes"]:
            file_path = change["file_path"]
            content   = change["new_content"]

            if not content.strip():
                all_errors.append(f"{file_path}: File is empty")
                continue

            if file_path.endswith(".py"):
                all_errors.extend(validate_python_syntax(content, file_path))

            if "import" not in content and file_path.endswith(".py"):
                all_warnings.append(f"{file_path}: No imports found")

        passed = len(all_errors) == 0

        validation_result = ValidationResult(
            passed=passed,
            errors=all_errors,
            warnings=all_warnings
        )

        publish_event(StreamEvent(
            event_type=EventType.VALIDATOR_COMPLETED,
            session_id=state["session_id"],
            message=f"Validation {'passed' if passed else 'failed'}: {len(all_errors)} errors",
            data={
                "passed":   passed,
                "errors":   all_errors,
                "warnings": all_warnings
            }
        ))

        logger.info("validation_done", passed=passed, errors=len(all_errors))

        return {
            **state,
            "validation_result": validation_result,
            "status":            AgentStatus.COMMITTING if passed else AgentStatus.GENERATING,
            "logs":              state["logs"] + [f"Validation {'passed' if passed else 'failed'}: {len(all_errors)} errors"]
        }

    except Exception as e:
        logger.error("validator_error", error=str(e))
        return {
            **state,
            "status":        AgentStatus.FAILED,
            "error_message": f"Validator failed: {str(e)}"
        }
