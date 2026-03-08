"""FastMCP Todo Server – exposes CRUD operations as MCP tools.

Persists todos in PostgreSQL via SQLAlchemy.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastmcp import FastMCP

from app.database import SessionLocal
from app.models.todo import Todo

# ── FastMCP server instance ──
todo_mcp = FastMCP(
    name="Todo Server",
    instructions=(
        "A Todo management service. Use the provided tools to "
        "create, list, update, and delete tasks."
    ),
)


@todo_mcp.tool()
def create_task(title: str, description: str = "") -> dict:
    """Create a new todo task.

    Args:
        title: The title of the task.
        description: Optional description of the task.

    Returns:
        The created task object.
    """
    db = SessionLocal()
    try:
        todo = Todo(
            id=str(uuid4())[:8],
            title=title,
            description=description,
        )
        db.add(todo)
        db.commit()
        db.refresh(todo)
        return todo.to_dict()
    finally:
        db.close()


@todo_mcp.tool()
def list_tasks(include_completed: bool = True) -> list[dict]:
    """List all todo tasks.

    Args:
        include_completed: Whether to include completed tasks.

    Returns:
        A list of task objects.
    """
    db = SessionLocal()
    try:
        query = db.query(Todo)
        if not include_completed:
            query = query.filter(Todo.completed == False)
        return [t.to_dict() for t in query.all()]
    finally:
        db.close()


@todo_mcp.tool()
def get_task(task_id: str) -> Optional[dict]:
    """Get a specific task by ID.

    Args:
        task_id: The ID of the task to retrieve.

    Returns:
        The task object or None if not found.
    """
    db = SessionLocal()
    try:
        todo = db.query(Todo).filter(Todo.id == task_id).first()
        return todo.to_dict() if todo else None
    finally:
        db.close()


@todo_mcp.tool()
def update_task(
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    completed: Optional[bool] = None,
) -> Optional[dict]:
    """Update an existing task.

    Args:
        task_id: The ID of the task to update.
        title: New title (optional).
        description: New description (optional).
        completed: New completion status (optional).

    Returns:
        The updated task object or None if not found.
    """
    db = SessionLocal()
    try:
        todo = db.query(Todo).filter(Todo.id == task_id).first()
        if todo is None:
            return None
        if title is not None and title != "":
            todo.title = title
        if description is not None and description != "":
            todo.description = description
        if completed is not None:
            todo.completed = completed
        todo.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(todo)
        return todo.to_dict()
    finally:
        db.close()


@todo_mcp.tool()
def delete_task(task_id: str) -> dict:
    """Delete a task by ID.

    Args:
        task_id: The ID of the task to delete.

    Returns:
        A confirmation message.
    """
    db = SessionLocal()
    try:
        todo = db.query(Todo).filter(Todo.id == task_id).first()
        if todo:
            db.delete(todo)
            db.commit()
            return {"deleted": True, "task_id": task_id}
        return {"deleted": False, "task_id": task_id, "error": "Task not found"}
    finally:
        db.close()
