from mcp_tools.base_tool import BaseTool
from mcp_tools.repo_tool import RepoTool
from mcp_tools.github_tool import GithubTool
from mcp_tools.rag_tool import RAGTool
from mcp_tools.validation_tool import ValidationTool
from mcp_tools.codegen_tool import CodegenTool

# Tool registry — all available tools
TOOLS = {
    "repo_tool":       RepoTool(),
    "github_tool":     GithubTool(),
    "rag_tool":        RAGTool(),
    "validation_tool": ValidationTool(),
    "codegen_tool":    CodegenTool()
}


def get_tool(name: str) -> BaseTool:
    """
    Returns a tool by name.
    Usage: get_tool("repo_tool").safe_execute({...})
    """
    tool = TOOLS.get(name)
    if not tool:
        raise ValueError(f"Tool not found: {name}")
    return tool
