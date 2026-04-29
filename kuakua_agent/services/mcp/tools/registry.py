import logging
from typing import list

logger = logging.getLogger(__name__)

class ToolRegistry:
    """Registry for MCP tools."""

    def __init__(self):
        self._tools = {}

    def register(self, tool: dict):
        """Register a tool."""
        name = tool.get("name")
        self._tools[name] = tool
        logger.info(f"Registered tool: {name}")

    def get_tool(self, name: str) -> dict:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        """List all registered tools."""
        return list(self._tools.values())

# Global registry instance
registry = ToolRegistry()
