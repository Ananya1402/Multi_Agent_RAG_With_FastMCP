"""Tool Agent – handles weather lookups and FastMCP Todo operations."""

import json
import logging

import httpx

from app.config import settings
from app.mcp.client import call_mcp_tool

logger = logging.getLogger(__name__)


# ── Weather Tool ──


# WMO Weather interpretation codes → descriptions
_WMO_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "depositing rime fog",
    51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
    61: "slight rain", 63: "moderate rain", 65: "heavy rain",
    71: "slight snow", 73: "moderate snow", 75: "heavy snow",
    80: "slight rain showers", 81: "moderate rain showers", 82: "violent rain showers",
    95: "thunderstorm", 96: "thunderstorm with slight hail", 99: "thunderstorm with heavy hail",
}


async def get_weather(city: str | None = None) -> dict:
    """Fetch current weather for a city using Open-Meteo (free, no API key).

    Steps:
      1. Geocode city name → latitude/longitude via Open-Meteo Geocoding API.
      2. Fetch current weather via Open-Meteo Forecast API.
    """
    city = city or settings.WEATHER_DEFAULT_CITY

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Step 1: Geocode city → coordinates
            geo_resp = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1, "language": "en"},
            )
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()

            if not geo_data.get("results"):
                return {
                    "city": city,
                    "temperature": 0,
                    "feels_like": 0,
                    "humidity": 0,
                    "description": "City not found",
                    "wind_speed": 0,
                    "note": f"Could not geocode city: {city}",
                }

            location = geo_data["results"][0]
            lat = location["latitude"]
            lon = location["longitude"]
            resolved_name = location.get("name", city)

            # Step 2: Fetch current weather
            weather_resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
                },
            )
            weather_resp.raise_for_status()
            current = weather_resp.json()["current"]

            weather_code = current.get("weather_code", 0)
            description = _WMO_CODES.get(weather_code, f"code {weather_code}")

            return {
                "city": resolved_name,
                "temperature": current["temperature_2m"],
                "feels_like": current["apparent_temperature"],
                "humidity": current["relative_humidity_2m"],
                "description": description,
                "wind_speed": current["wind_speed_10m"],
            }
    except Exception as e:
        logger.warning("Open-Meteo API call failed: %s", e)
        return {
            "city": city,
            "temperature": 0,
            "feels_like": 0,
            "humidity": 0,
            "description": "weather service unavailable",
            "wind_speed": 0,
            "note": f"Error fetching weather: {str(e)}",
        }


def format_weather_response(weather: dict) -> str:
    """Format weather data into a human-readable string."""
    return (
        f"Weather in {weather['city']}:\n"
        f"  Temperature: {weather['temperature']}°C "
        f"(feels like {weather['feels_like']}°C)\n"
        f"  Humidity: {weather['humidity']}%\n"
        f"  Conditions: {weather['description']}\n"
        f"  Wind Speed: {weather['wind_speed']} m/s"
    )


# ── Todo Tools (via FastMCP) ──


async def _resolve_task_id(params: dict) -> dict:
    """If task_id is missing but title_keyword is present, search tasks by keyword."""
    if params.get("task_id"):
        return params

    keyword = params.pop("title_keyword", None)
    if not keyword:
        return params

    # List all tasks and find the best match by keyword
    all_tasks = await call_mcp_tool("list_tasks", {"include_completed": True})
    if not isinstance(all_tasks, list):
        return params

    keyword_lower = keyword.lower()
    for task in all_tasks:
        title = (task.get("title") or "").lower().strip()
        if not title:
            continue  # skip tasks with blank titles
        if keyword_lower in title or title in keyword_lower:
            params["task_id"] = task["id"]
            logger.info("Resolved keyword '%s' to task_id '%s' (%s)", keyword, task["id"], task["title"])
            return params

    # No exact substring match — try word overlap
    kw_words = set(keyword_lower.split())
    best_match = None
    best_score = 0
    for task in all_tasks:
        title = (task.get("title") or "").lower().strip()
        if not title:
            continue  # skip tasks with blank titles
        title_words = set(title.split())
        overlap = len(kw_words & title_words)
        if overlap > best_score:
            best_score = overlap
            best_match = task

    if best_match and best_score > 0:
        params["task_id"] = best_match["id"]
        logger.info("Resolved keyword '%s' to task_id '%s' (%s) via word overlap", keyword, best_match["id"], best_match["title"])
    else:
        logger.warning("Could not resolve keyword '%s' to any task", keyword)

    return params


async def handle_todo_operation(operation: str, **kwargs) -> str:
    """Route a todo operation to the FastMCP Todo server.

    Args:
        operation: One of 'create', 'list', 'update', 'delete', 'get'.
        **kwargs: Arguments for the specific operation.

    Returns:
        Formatted string result.
    """
    tool_map = {
        "create": "create_task",
        "list": "list_tasks",
        "get": "get_task",
        "update": "update_task",
        "delete": "delete_task",
    }

    tool_name = tool_map.get(operation)
    if not tool_name:
        return f"Unknown todo operation: {operation}"

    # Resolve task by keyword if no task_id provided
    if operation in ("update", "delete", "get"):
        kwargs = await _resolve_task_id(kwargs)
        if not kwargs.get("task_id"):
            return f"Could not find a matching task. Try listing your tasks first with 'show my tasks'."

    # Remove title_keyword before calling MCP (not a valid tool param)
    kwargs.pop("title_keyword", None)

    # For updates, strip empty-string values so they don't overwrite existing data
    if operation == "update":
        kwargs = {k: v for k, v in kwargs.items() if v is not None and v != ""}

    try:
        result = await call_mcp_tool(tool_name, kwargs)
        # Add a human-friendly message based on the operation
        return json.dumps(_add_todo_message(operation, result), indent=2)
    except Exception as e:
        logger.error("MCP tool call failed: %s", e)
        return f"Error performing todo operation: {str(e)}"


def _add_todo_message(operation: str, result) -> dict:
    """Wrap the MCP result with a human-readable message."""
    if operation == "create" and isinstance(result, dict):
        title = result.get("title") or result.get("description") or "Untitled"
        return {"message": f"Task '{title}' created successfully.", "task": result}

    if operation == "list" and isinstance(result, list):
        count = len(result)
        if count == 0:
            return {"message": "You have no tasks.", "tasks": []}
        completed = sum(1 for t in result if t.get("completed"))
        return {
            "message": f"You have {count} task(s) ({completed} completed, {count - completed} pending).",
            "tasks": result,
        }

    if operation == "get" and isinstance(result, dict):
        title = result.get("title") or result.get("description") or "Untitled"
        status = "completed" if result.get("completed") else "pending"
        return {"message": f"Task '{title}' is {status}.", "task": result}

    if operation == "update" and isinstance(result, dict):
        title = result.get("title") or result.get("description") or "Untitled"
        status = "completed" if result.get("completed") else "pending"
        return {"message": f"Task '{title}' updated successfully. Status: {status}.", "task": result}

    if operation == "delete" and isinstance(result, dict):
        if result.get("deleted"):
            return {"message": f"Task '{result.get('task_id')}' deleted successfully.", "result": result}
        return {"message": f"Could not delete task: {result.get('error', 'unknown error')}.", "result": result}

    return {"message": "Done.", "result": result}


async def handle_tool_query(query: str, intent_detail: dict) -> str:
    """Process a tool-related query based on detected intent.

    Args:
        query: Original user query.
        intent_detail: Dict with 'tool' (weather/todo) and optional params.

    Returns:
        Response string.
    """
    tool = intent_detail.get("tool", "")

    if tool == "weather":
        city = intent_detail.get("city", settings.WEATHER_DEFAULT_CITY)
        weather = await get_weather(city)
        msg = format_weather_response(weather)
        return json.dumps({"message": msg, "weather": weather})

    elif tool == "todo":
        operation = intent_detail.get("operation", "list")
        params = intent_detail.get("params", {})
        return await handle_todo_operation(operation, **params)

    return f"Unknown tool request: {tool}"
