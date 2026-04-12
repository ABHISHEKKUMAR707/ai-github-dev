import ast
from mcp_tools.base_tool import BaseTool
from typing import Any, Dict, List
import structlog

logger = structlog.get_logger()


class ValidationTool(BaseTool):
    name        = "validation_tool"
    description = "Validate generated code for syntax and logic errors"

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action = input_data.get("action")

        if action == "validate_file":
            return self._validate_file(input_data)
        elif action == "validate_all":
            return self._validate_all(input_data)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    def _validate_file(self, data: Dict) -> Dict:
        """
        Validates a single file.
        Input:
            file_path: str
            content:   str
        """
        file_path = data["file_path"]
        content   = data["content"]
        errors    = []
        warnings  = []

        # Check empty file
        if not content.strip():
            errors.append(f"{file_path}: File is empty")
            return {
                "success":  False,
                "passed":   False,
                "errors":   errors,
                "warnings": warnings
            }

        # Python syntax check
        if file_path.endswith(".py"):
            errors.extend(
                self._check_python_syntax(file_path, content)
            )
            warnings.extend(
                self._check_python_style(file_path, content)
            )

        passed = len(errors) == 0

        logger.info(
            "file_validated",
            file=file_path,
            passed=passed,
            errors=len(errors)
        )

        return {
            "success":  True,
            "passed":   passed,
            "errors":   errors,
            "warnings": warnings
        }

    def _validate_all(self, data: Dict) -> Dict:
        """
        Validates multiple files at once.
        Input:
            files: list of {file_path, content}
        """
        all_errors   = []
        all_warnings = []

        for file in data.get("files", []):
            result = self._validate_file(file)
            all_errors.extend(result["errors"])
            all_warnings.extend(result["warnings"])

        passed = len(all_errors) == 0

        return {
            "success":  True,
            "passed":   passed,
            "errors":   all_errors,
            "warnings": all_warnings,
            "files":    len(data.get("files", []))
        }

    def _check_python_syntax(
        self,
        file_path: str,
        content:   str
    ) -> List[str]:
        """Uses AST to check Python syntax."""
        errors = []
        try:
            ast.parse(content)
        except SyntaxError as e:
            errors.append(
                f"{file_path}: SyntaxError at line {e.lineno}: {e.msg}"
            )
        except Exception as e:
            errors.append(f"{file_path}: Parse error: {str(e)}")
        return errors

    def _check_python_style(
        self,
        file_path: str,
        content:   str
    ) -> List[str]:
        """Basic style checks — non blocking warnings."""
        warnings = []

        if "import" not in content:
            warnings.append(f"{file_path}: No imports found")

        if "def " not in content and "class " not in content:
            warnings.append(f"{file_path}: No functions or classes found")

        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                warnings.append(f"{file_path}: Line {i} exceeds 120 chars")

        return warnings
