"""Parent Agent (Orchestrator) – routes user queries to the correct specialist agent.

Uses LangGraph to define a state machine with:
  1. Intent Detection  → classify the query
  2. RAG Agent         → FAQ questions
  3. Tool Agent        → weather / todo operations
  4. Response          → final answer
"""

import json
import logging
from typing import TypedDict, Literal

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from app.config import settings
from app.agents.rag_agent import handle_rag_query
from app.agents.tool_agent import handle_tool_query

logger = logging.getLogger(__name__)

# ── State schema ──


class AgentState(TypedDict):
    """State passed between graph nodes."""
    query: str
    intent: str  # "faq", "weather", "todo", "unknown"
    intent_detail: dict
    response: str


# ── Intent Detection ──

INTENT_SYSTEM_PROMPT = """You are an intent classifier. Given a user query, classify it into one of these categories:

1. "faq" - Questions about products, services, BigRock, domains, hosting, affiliates, website, email, or general FAQ questions
2. "weather" - Questions about weather, temperature, forecast for a city
3. "todo" - Requests to create, list, view, update, or delete tasks/todos
4. "unknown" - Cannot determine the intent

Respond ONLY with a JSON object (no markdown, no extra text):
{{
  "intent": "<faq|weather|todo|unknown>",
  "tool": "<weather|todo|null>",
  "city": "<city name if weather, else null>",
  "operation": "<create|list|get|update|delete if todo, else null>",
  "params": {{<todo params if applicable, else empty object>}}
}}

For todo operations, extract these params:
- create: {{"title": "...", "description": "..."}}
- update: {{"task_id": "...", "title_keyword": "...", "title": "...", "completed": true/false}}
- delete: {{"task_id": "...", "title_keyword": "..."}}
- get: {{"task_id": "...", "title_keyword": "..."}}
- list: {{"include_completed": true/false}}

IMPORTANT: If the user refers to a task by name/description instead of ID, put the descriptive keywords in "title_keyword" and omit "task_id".
If the user provides an actual ID (like "abc12345"), put it in "task_id".
"""


async def detect_intent(state: AgentState) -> AgentState:
    """Detect the intent of the user query using the LLM."""
    query = state["query"]
    logger.info("Detecting intent for: %s", query[:100])

    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=0,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", INTENT_SYSTEM_PROMPT),
            ("human", "{query}"),
        ]
    )

    chain = prompt | llm
    response = await chain.ainvoke({"query": query})

    try:
        parsed = json.loads(response.content.strip())
        intent = parsed.get("intent", "unknown")
        logger.info("Detected intent: %s", intent)
        return {
            **state,
            "intent": intent,
            "intent_detail": parsed,
        }
    except json.JSONDecodeError:
        logger.warning("Failed to parse intent response: %s", response.content)
        return {
            **state,
            "intent": "unknown",
            "intent_detail": {},
        }


# ── Agent Nodes ──


async def rag_node(state: AgentState) -> AgentState:
    """Route to the RAG agent for FAQ queries."""
    response = await handle_rag_query(state["query"])
    return {**state, "response": response}


async def tool_node(state: AgentState) -> AgentState:
    """Route to the Tool agent for weather/todo queries."""
    response = await handle_tool_query(state["query"], state["intent_detail"])
    return {**state, "response": response}


async def unknown_node(state: AgentState) -> AgentState:
    """Handle unclassifiable queries."""
    return {
        **state,
        "response": (
            "I'm not sure how to help with that. I can assist with:\n"
            "- FAQ questions about BigRock products and services\n"
            "- Weather information for any city\n"
            "- Task/todo management (create, list, update, delete)"
        ),
    }


# ── Router ──


def route_by_intent(state: AgentState) -> Literal["rag_node", "tool_node", "unknown_node"]:
    """Route to the appropriate agent based on detected intent."""
    intent = state.get("intent", "unknown")
    if intent == "faq":
        return "rag_node"
    elif intent in ("weather", "todo"):
        return "tool_node"
    else:
        return "unknown_node"


# ── Build the Graph ──


def build_orchestrator_graph() -> StateGraph:
    """Construct the LangGraph orchestrator."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("detect_intent", detect_intent)
    graph.add_node("rag_node", rag_node)
    graph.add_node("tool_node", tool_node)
    graph.add_node("unknown_node", unknown_node)

    # Set entry point
    graph.set_entry_point("detect_intent")

    # Conditional routing after intent detection
    graph.add_conditional_edges(
        "detect_intent",
        route_by_intent,
        {
            "rag_node": "rag_node",
            "tool_node": "tool_node",
            "unknown_node": "unknown_node",
        },
    )

    # All agent nodes lead to END
    graph.add_edge("rag_node", END)
    graph.add_edge("tool_node", END)
    graph.add_edge("unknown_node", END)

    return graph.compile()


# Module-level compiled graph
_orchestrator = None


def get_orchestrator():
    """Return the compiled orchestrator graph (singleton)."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = build_orchestrator_graph()
    return _orchestrator


async def process_query(query: str) -> str:
    """Main entry point – process a user query through the orchestrator.

    Args:
        query: The user's natural language query.

    Returns:
        The final response string.
    """
    orchestrator = get_orchestrator()
    initial_state: AgentState = {
        "query": query,
        "intent": "",
        "intent_detail": {},
        "response": "",
    }

    result = await orchestrator.ainvoke(initial_state)
    return result.get("response", "An error occurred processing your request.")
