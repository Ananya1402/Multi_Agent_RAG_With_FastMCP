"""Weather API routes."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.auth.jwt_handler import get_current_user
from app.weather import controllers

router = APIRouter(prefix="/weather", tags=["Weather"])


class WeatherResponse(BaseModel):
    city: str
    temperature: float
    feels_like: float
    humidity: int
    description: str
    wind_speed: float
    note: Optional[str] = None


@router.get("", response_model=WeatherResponse)
async def get_weather(
    city: Optional[str] = Query(None, description="City name (defaults to configured city)"),
    current_user: dict = Depends(get_current_user),
):
    """Return current weather for the configured or specified city.

    Requires JWT authentication.
    """
    return await controllers.handle_weather(city)
