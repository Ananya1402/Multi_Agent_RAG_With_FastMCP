"""FastMCP client – connects to the Todo MCP server for tool invocations."""

import json
import logging
from typing import Optional

from fastmcp import Client
from app.mcp.todo_server import todo_mcp

logger = logging.getLogger(__name__)

# Use in-memory transport by passing the FastMCP server directly
_client = Client(todo_mcp)


async def call_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """Call a tool on the FastMCP Todo server.

    Args:
        tool_name: Name of the MCP tool to invoke.
        arguments: Dictionary of arguments for the tool.

    Returns:
        The tool result as a dictionary.
    """
    async with _client:
        result = await _client.call_tool(tool_name, arguments)
        # FastMCP 3.x returns a CallToolResult with a .content list
        if result.content and hasattr(result.content[0], "text"):
            text = result.content[0].text
            # Handle null/None responses (e.g. task not found)
            if text == "null" or text is None:
                return None
            try:
                return json.loads(text)
            except (json.JSONDecodeError, IndexError):
                return {"result": text}
        # Empty content means the tool returned None
        return None


async def list_mcp_tools() -> list[dict]:
    """List available tools on the MCP server."""
    async with _client:
        tools = await _client.list_tools()
        return [
            {
                "name": t.name,
                "description": t.description,
            }
            for t in tools
        ]
