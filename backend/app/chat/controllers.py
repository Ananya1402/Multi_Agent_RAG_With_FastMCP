"""Chat controller – orchestrates query processing."""

import json
import logging

from app.agents.orchestrator import process_query

logger = logging.getLogger(__name__)


async def handle_chat(query: str, username: str) -> dict:
    """Process a chat query through the multi-agent orchestrator.

    Args:
        query: The user's natural language query.
        username: The authenticated user's username.

    Returns:
        Dict with query, response, and metadata.
    """
    logger.info("Chat from user '%s': %s", username, query[:100])
    response = await process_query(query)

    # If the response is a JSON string, parse it into a proper object
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except (json.JSONDecodeError, ValueError):
            pass  # Keep as plain string (e.g. RAG text answers)

    return {
        "query": query,
        "response": response,
        "user": username,
    }
