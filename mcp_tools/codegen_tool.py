from mcp_tools.base_tool import BaseTool
from config.claude_client import call_claude
from typing import Any, Dict, List
import re
import structlog

logger = structlog.get_logger()

CODEGEN_SYSTEM_PROMPT = """
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


class CodegenTool(BaseTool):
    name        = "codegen_tool"
    description = "Generate production-quality code using Claude API"

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action = input_data.get("action")

        if action == "generate":
            return self._generate(input_data)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    def _generate(self, data: Dict) -> Dict:
        """
        Generates code using Claude API.
        Input:
            context:      str  (assembled context from context builder)
            user_intent:  str  (what user wants)
            plan:         list (implementation steps)
        """
        context     = data["context"]
        user_intent = data["user_intent"]
        plan        = data.get("plan", [])

        prompt = f"""
Here is the repository context and what needs to be implemented:

{context}

User Request: {user_intent}

Implementation Plan:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(plan))}

Now implement all the steps in the plan.
Generate complete, production-ready code for each file.
"""
        logger.info("generating_code", intent=user_intent)

        response = call_claude(
            prompt=prompt,
            system=CODEGEN_SYSTEM_PROMPT,
            max_tokens=8000
        )

        file_changes = self._parse_response(response)

        logger.info("code_generated", files=len(file_changes))

        return {
            "success":      True,
            "file_changes": file_changes,
            "count":        len(file_changes)
        }

    def _parse_response(self, response: str) -> List[Dict]:
        """Parses Claude response into file changes."""
        changes = []
        parts   = response.split("FILE:")

        for part in parts[1:]:
            try:
                lines     = part.strip().split("\n")
                file_path = lines[0].strip()

                action_line = lines[1].strip() if len(lines) > 1 else ""
                action      = "create"
                if "ACTION:" in action_line:
                    action = action_line.replace("ACTION:", "").strip().lower()

                code_match = re.search(
                    r"```(?:python|javascript|typescript|)?\n(.*?)```",
                    part,
                    re.DOTALL
                )

                if code_match:
                    content = code_match.group(1).strip()
                    changes.append({
                        "file_path":        file_path,
                        "original_content": "",
                        "new_content":      content,
                        "change_type":      action
                    })
            except Exception:
                continue

        return changes
