"""Happy-path tests for the Weather API."""

from fastapi.testclient import TestClient


class TestWeatherAPI:
    """Weather endpoint tests."""

    def test_get_weather_default_city(self, client: TestClient, auth_headers: dict):
        """GET /weather should return weather for the default city."""
        resp = client.get("/weather", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "city" in data
        assert "temperature" in data
        assert "humidity" in data
        assert "description" in data
        assert "wind_speed" in data

    def test_get_weather_with_city(self, client: TestClient, auth_headers: dict):
        """GET /weather?city=Paris should return weather for Paris."""
        resp = client.get("/weather", params={"city": "Paris"}, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["city"] == "Paris"

    def test_weather_requires_auth(self, client: TestClient):
        """Weather endpoint should require JWT."""
        resp = client.get("/weather")
        assert resp.status_code == 401
