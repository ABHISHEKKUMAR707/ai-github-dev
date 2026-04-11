import os
import git
from agent.state import AgentState, AgentStatus
import structlog

logger = structlog.get_logger()

REPOS_DIR = 'repos'


def get_repo_structure(repo_path: str) -> dict:
    '''
    Walks the repo folder and builds a directory tree.
    Skips .git, __pycache__, node_modules etc.
    '''
    structure = {}
    skip_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv'}

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        rel_root = os.path.relpath(root, repo_path)
        structure[rel_root] = files

    return structure


def run(state: AgentState) -> AgentState:
    '''
    Retrieval node — clones repo and reads structure.
    Reads:  state.repo_url, state.github_token
    Writes: state.repo_structure, state.status, state.logs
    '''
    logger.info('retrieval_started', session_id=state['session_id'])

    try:
        os.makedirs(REPOS_DIR, exist_ok=True)

        # Build authenticated clone URL
        repo_url   = state['repo_url']
        token      = state['github_token']
        auth_url   = repo_url.replace(
            'https://',
            f'https://{token}@'
        )

        # Folder name from repo URL
        repo_name  = repo_url.rstrip('/').split('/')[-1]
        local_path = os.path.join(REPOS_DIR, f"{state['session_id']}_{repo_name}")

        # Clone if not already cloned
        if not os.path.exists(local_path):
            logger.info('cloning_repo', repo=repo_url)
            git.Repo.clone_from(auth_url, local_path)
        else:
            logger.info('repo_already_exists', path=local_path)

        # Build structure map
        structure = get_repo_structure(local_path)

        logger.info('retrieval_done', files=sum(len(v) for v in structure.values()))

        return {
            **state,
            'repo_structure': structure,
            'status':         AgentStatus.BUILDING,
            'logs':           state['logs'] + [f'Repo cloned: {repo_name}']
        }

    except Exception as e:
        logger.error('retrieval_failed', error=str(e))
        return {
            **state,
            'status':        AgentStatus.FAILED,
            'error_message': f'Retrieval failed: {str(e)}'
        }
