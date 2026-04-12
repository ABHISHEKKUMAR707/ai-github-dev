from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any, Dict


class ToolInput(BaseModel):
    """Base class for all tool inputs."""
    pass


class ToolOutput(BaseModel):
    """Base class for all tool outputs."""
    success: bool
    error:   str = ""


class BaseTool(ABC):
    """
    Abstract base class for all MCP tools.
    Every tool must implement:
    - name: unique tool identifier
    - description: what the tool does
    - execute(): main logic
    """
    name:        str = ""
    description: str = ""

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main tool logic.
        Must return dict with at least:
        - success: bool
        - error: str (empty if success)
        """
        pass

    def safe_execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wraps execute() with error handling.
        Always returns a valid response.
        """
        try:
            return self.execute(input_data)
        except Exception as e:
            return {
                "success": False,
                "error":   f"{self.name} failed: {str(e)}"
            }
