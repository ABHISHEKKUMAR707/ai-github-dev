from agent.state import AgentState, AgentStatus
import structlog

logger = structlog.get_logger()


def run(state: AgentState) -> AgentState:
    '''
    Decision node — routes agent based on validation result.
    Reads:  state.validation_result, state.retry_count
    Writes: state.retry_count, state.status
    '''
    logger.info('decision_started', session_id=state['session_id'])

    validation = state['validation_result']

    # Validation passed — move to commit
    if validation and validation['passed']:
        logger.info('decision_commit', session_id=state['session_id'])
        return {
            **state,
            'status': AgentStatus.COMMITTING,
            'logs':   state['logs'] + ['Decision: validation passed, moving to commit']
        }

    # Validation failed — check retries
    retry_count = state['retry_count']
    max_retries = state['max_retries']

    if retry_count < max_retries:
        new_retry = retry_count + 1
        logger.warning(
            'decision_retry',
            attempt=new_retry,
            max=max_retries,
            errors=validation['errors'] if validation else []
        )
        return {
            **state,
            'retry_count': new_retry,
            'status':      AgentStatus.GENERATING,
            'logs':        state['logs'] + [f'Decision: retry {new_retry}/{max_retries}']
        }

    # No retries left — fail
    logger.error('decision_failed', session_id=state['session_id'])
    return {
        **state,
        'status':        AgentStatus.FAILED,
        'error_message': f'Validation failed after {max_retries} retries. Errors: {validation["errors"] if validation else "unknown"}',
        'logs':          state['logs'] + ['Decision: max retries reached, failing']
    }


def route(state: AgentState) -> str:
    '''
    Called by LangGraph to decide which edge to follow.
    Returns: 'commit' | 'retry' | 'fail'
    '''
    validation  = state['validation_result']
    retry_count = state['retry_count']
    max_retries = state['max_retries']

    if validation and validation['passed']:
        return 'commit'

    if retry_count < max_retries:
        return 'retry'

    return 'fail'
