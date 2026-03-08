"""Chat API routes."""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.jwt_handler import get_current_user
from app.chat import controllers

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    query: str
    response: Any
    user: str


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Accept a query and route it through the parent (orchestrator) agent.

    The orchestrator detects intent and delegates to:
    - **RAG Agent** for FAQ queries
    - **Tool Agent** for weather or todo operations

    Requires JWT authentication.
    """
    result = await controllers.handle_chat(
        query=request.query,
        username=current_user.get("sub", "unknown"),
    )
    return result
