"""Todo API routes – REST endpoints backed by the FastMCP Todo server."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.jwt_handler import get_current_user
from app.todo import controllers

router = APIRouter(prefix="/todos", tags=["Todos"])


# ── Request / Response schemas ──


class CreateTaskRequest(BaseModel):
    title: str
    description: str = ""


class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None


# ── Endpoints ──


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_task(
    request: CreateTaskRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a new task. Requires JWT authentication."""
    return await controllers.create_task(request.title, request.description)


@router.get("")
async def list_tasks(
    include_completed: bool = True,
    current_user: dict = Depends(get_current_user),
):
    """List all tasks. Requires JWT authentication."""
    return await controllers.list_tasks(include_completed)


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific task by ID. Requires JWT authentication."""
    result = await controllers.get_task(task_id)
    if result is None or result == "null":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return result


@router.put("/{task_id}")
async def update_task(
    task_id: str,
    request: UpdateTaskRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update a task. Requires JWT authentication."""
    result = await controllers.update_task(
        task_id, request.title, request.description, request.completed
    )
    if result is None or result == "null":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return result


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a task. Requires JWT authentication."""
    result = await controllers.delete_task(task_id)
    if result and not result.get("deleted"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return result
