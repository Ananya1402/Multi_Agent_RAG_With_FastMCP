"""Weather controller – fetches weather data."""

from app.agents.tool_agent import get_weather


async def handle_weather(city: str | None = None) -> dict:
    """Fetch current weather for a city.

    Args:
        city: City name. Defaults to configured WEATHER_DEFAULT_CITY.

    Returns:
        Weather data dict.
    """
    return await get_weather(city)
