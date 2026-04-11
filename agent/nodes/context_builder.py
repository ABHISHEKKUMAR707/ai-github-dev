import os
from agent.state import AgentState, AgentStatus
import structlog

logger = structlog.get_logger()

REPOS_DIR = 'repos'


def read_file_content(file_path: str) -> str:
    '''Safely reads a file and returns its content.'''
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return ''


def find_relevant_files(repo_structure: dict, plan: list) -> list:
    '''
    Looks at the plan steps and finds existing files
    that are mentioned or likely related.
    '''
    relevant = []
    plan_text = ' '.join(plan).lower()

    for folder, files in repo_structure.items():
        for file in files:
            file_lower = file.lower()
            # Include if file is mentioned in plan
            if any(word in plan_text for word in [
                file_lower,
                file_lower.replace('.py', ''),
                folder.lower()
            ]):
                relevant.append(os.path.join(folder, file))

            # Always include key project files
            if file in ['app.py', 'main.py', 'requirements.txt',
                        'README.md', '__init__.py']:
                if os.path.join(folder, file) not in relevant:
                    relevant.append(os.path.join(folder, file))

    return relevant[:10]  # max 10 files to avoid token overflow


def run(state: AgentState) -> AgentState:
    '''
    Context Builder node — reads relevant files and builds prompt.
    Reads:  state.repo_structure, state.plan
    Writes: state.assembled_context, state.status
    '''
    logger.info('context_builder_started', session_id=state['session_id'])

    try:
        repo_name  = state['repo_url'].rstrip('/').split('/')[-1]
        local_path = os.path.join(
            REPOS_DIR,
            f"{state['session_id']}_{repo_name}"
        )

        relevant_files = find_relevant_files(
            state['repo_structure'],
            state['plan']
        )

        # Build context string
        context_parts = []
        context_parts.append(f'Repository: {state["repo_url"]}')
        context_parts.append(f'\nDeveloper Request: {state["cleaned_intent"]}')
        context_parts.append(f'\nImplementation Plan:')

        for i, step in enumerate(state['plan'], 1):
            context_parts.append(f'  {i}. {step}')

        context_parts.append('\nExisting Relevant Files:')

        for rel_path in relevant_files:
            full_path = os.path.join(local_path, rel_path)
            content   = read_file_content(full_path)
            if content:
                context_parts.append(f'\n--- {rel_path} ---')
                context_parts.append(content[:2000])  # max 2000 chars per file

        assembled = '\n'.join(context_parts)

        logger.info('context_built', files=len(relevant_files))

        return {
            **state,
            'assembled_context': assembled,
            'status':            AgentStatus.GENERATING,
            'logs':              state['logs'] + [f'Context built from {len(relevant_files)} files']
        }

    except Exception as e:
        logger.error('context_builder_failed', error=str(e))
        return {
            **state,
            'status':        AgentStatus.FAILED,
            'error_message': f'Context builder failed: {str(e)}'
        }
