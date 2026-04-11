from typing import TypedDict, List, Optional, Dict
from enum import Enum


class AgentStatus(str, Enum):
    PLANNING   = 'planning'
    RETRIEVING = 'retrieving'
    BUILDING   = 'building_context'
    GENERATING = 'generating_code'
    VALIDATING = 'validating'
    COMMITTING = 'committing'
    DONE       = 'done'
    FAILED     = 'failed'


class FileChange(TypedDict):
    file_path:      str    # e.g. 'attendance/tracker.py'
    original_content: str  # what was there before
    new_content:    str    # what we are writing
    change_type:    str    # 'create' or 'modify' or 'delete'


class ValidationResult(TypedDict):
    passed:   bool
    errors:   List[str]
    warnings: List[str]


class AgentState(TypedDict):
    # Identity
    session_id:    str
    user_id:       int
    repo_url:      str
    github_token:  str

    # Input
    raw_input:     str
    cleaned_intent: str

    # Planning
    plan:          List[str]
    current_step:  int

    # Retrieval
    retrieved_chunks: List[Dict]
    repo_structure:   Dict

    # Context
    assembled_context: str

    # Code Generation
    file_changes:  List[FileChange]

    # Validation
    validation_result: Optional[ValidationResult]
    retry_count:   int
    max_retries:   int

    # Output
    branch_name:   Optional[str]
    pr_url:        Optional[str]
    status:        AgentStatus
    error_message: Optional[str]

    # Audit
    logs:          List[str]
