"""Todo controller – proxies CRUD operations to the FastMCP Todo server."""

import logging

from app.mcp.client import call_mcp_tool

logger = logging.getLogger(__name__)


async def create_task(title: str, description: str = "") -> dict:
    """Create a new task via FastMCP."""
    return await call_mcp_tool("create_task", {"title": title, "description": description})


async def list_tasks(include_completed: bool = True) -> list | dict:
    """List all tasks via FastMCP."""
    return await call_mcp_tool("list_tasks", {"include_completed": include_completed})


async def get_task(task_id: str) -> dict:
    """Get a specific task via FastMCP."""
    return await call_mcp_tool("get_task", {"task_id": task_id})


async def update_task(
    task_id: str,
    title: str | None = None,
    description: str | None = None,
    completed: bool | None = None,
) -> dict:
    """Update a task via FastMCP."""
    params = {"task_id": task_id}
    if title is not None:
        params["title"] = title
    if description is not None:
        params["description"] = description
    if completed is not None:
        params["completed"] = completed
    return await call_mcp_tool("update_task", params)


async def delete_task(task_id: str) -> dict:
    """Delete a task via FastMCP."""
    return await call_mcp_tool("delete_task", {"task_id": task_id})
