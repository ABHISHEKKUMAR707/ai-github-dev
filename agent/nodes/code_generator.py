import re
from agent.state import AgentState, AgentStatus, FileChange
from config.claude_client import call_claude
import structlog

logger = structlog.get_logger()

CODE_GEN_SYSTEM_PROMPT = '''
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
`python
# full file content here
`

FILE: path/to/existing.py
ACTION: modify
`python
# full updated file content here
`

Only output file blocks. No explanations outside the blocks.
'''


def parse_file_changes(response: str) -> list:
    '''
    Parses Claude response into list of FileChange objects.
    Looks for FILE: and ACTION: markers.
    '''
    changes = []

    # Split by FILE: marker
    parts = response.split('FILE:')

    for part in parts[1:]:  # skip first empty split
        try:
            lines      = part.strip().split('\n')
            file_path  = lines[0].strip()

            # Get action
            action_line = lines[1].strip() if len(lines) > 1 else ''
            action      = 'create'
            if 'ACTION:' in action_line:
                action = action_line.replace('ACTION:', '').strip().lower()

            # Extract code block
            code_match = re.search(r'`(?:python|javascript|typescript|)?\n(.*?)`', part, re.DOTALL)
            if code_match:
                content = code_match.group(1).strip()
                changes.append(FileChange(
                    file_path=file_path,
                    original_content='',
                    new_content=content,
                    change_type=action
                ))
        except Exception:
            continue

    return changes


def run(state: AgentState) -> AgentState:
    '''
    Code Generator node — asks Claude to write the code.
    Reads:  state.assembled_context
    Writes: state.file_changes, state.status
    '''
    logger.info('code_generator_started', session_id=state['session_id'])

    try:
        prompt = f'''
Here is the repository context and what needs to be implemented:

{state["assembled_context"]}

Now implement all the steps in the plan.
Generate complete, production-ready code for each file.
'''
        response = call_claude(
            prompt=prompt,
            system=CODE_GEN_SYSTEM_PROMPT,
            max_tokens=8000
        )

        file_changes = parse_file_changes(response)

        if not file_changes:
            raise ValueError('Claude returned no file changes')

        logger.info('code_generated', files=len(file_changes))

        return {
            **state,
            'file_changes': file_changes,
            'status':       AgentStatus.VALIDATING,
            'logs':         state['logs'] + [f'Generated {len(file_changes)} file changes']
        }

    except Exception as e:
        logger.error('code_generator_failed', error=str(e))
        return {
            **state,
            'status':        AgentStatus.FAILED,
            'error_message': f'Code generation failed: {str(e)}'
        }
