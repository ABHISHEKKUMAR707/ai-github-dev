import ast
from agent.state import AgentState, AgentStatus, ValidationResult
import structlog

logger = structlog.get_logger()


def validate_python_syntax(code: str, file_path: str) -> list:
    '''
    Uses Python AST parser to check for syntax errors.
    Returns list of error strings, empty if no errors.
    '''
    errors = []
    try:
        ast.parse(code)
    except SyntaxError as e:
        errors.append(f'{file_path}: SyntaxError at line {e.lineno}: {e.msg}')
    except Exception as e:
        errors.append(f'{file_path}: Parse error: {str(e)}')
    return errors


def validate_file(file_path: str, content: str) -> list:
    '''
    Validates a single file based on its extension.
    Currently supports Python — easy to extend later.
    '''
    errors = []

    if file_path.endswith('.py'):
        errors.extend(validate_python_syntax(content, file_path))

    # Basic checks for all files
    if not content.strip():
        errors.append(f'{file_path}: File is empty')

    return errors


def run(state: AgentState) -> AgentState:
    '''
    Validator node — checks all generated code for errors.
    Reads:  state.file_changes
    Writes: state.validation_result, state.status
    '''
    logger.info('validator_started', session_id=state['session_id'])

    try:
        all_errors   = []
        all_warnings = []

        for change in state['file_changes']:
            file_path = change['file_path']
            content   = change['new_content']

            errors = validate_file(file_path, content)
            all_errors.extend(errors)

            # Warnings — non blocking
            if 'import' not in content and file_path.endswith('.py'):
                all_warnings.append(f'{file_path}: No imports found')

        passed = len(all_errors) == 0

        validation_result = ValidationResult(
            passed=passed,
            errors=all_errors,
            warnings=all_warnings
        )

        if passed:
            logger.info('validation_passed', files=len(state['file_changes']))
        else:
            logger.warning('validation_failed', errors=all_errors)

        return {
            **state,
            'validation_result': validation_result,
            'status':            AgentStatus.COMMITTING if passed else AgentStatus.GENERATING,
            'logs':              state['logs'] + [
                f'Validation {"passed" if passed else "failed"}: {len(all_errors)} errors'
            ]
        }

    except Exception as e:
        logger.error('validator_error', error=str(e))
        return {
            **state,
            'status':        AgentStatus.FAILED,
            'error_message': f'Validator failed: {str(e)}'
        }
