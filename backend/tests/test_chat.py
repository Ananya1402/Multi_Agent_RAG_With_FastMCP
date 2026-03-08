"""Happy-path tests for the Chat API."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


class TestChatAPI:
    """Chat endpoint tests."""

    def test_chat_requires_auth(self, client: TestClient):
        """POST /chat should require JWT."""
        resp = client.post("/chat", json={"query": "hello"})
        assert resp.status_code == 401

    @patch("app.agents.orchestrator.process_query", new_callable=AsyncMock)
    def test_chat_faq_query(self, mock_process, client: TestClient, auth_headers: dict):
        """POST /chat with an FAQ query should return a response."""
        mock_process.return_value = "BigRock offers domain registration services."
        resp = client.post(
            "/chat",
            json={"query": "What is BigRock?"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "What is BigRock?"
        assert "response" in data
        assert data["user"] == "testuser"

    @patch("app.agents.orchestrator.process_query", new_callable=AsyncMock)
    def test_chat_weather_query(self, mock_process, client: TestClient, auth_headers: dict):
        """POST /chat with a weather query should return a response."""
        mock_process.return_value = "Weather in London: 22.5°C, partly cloudy."
        resp = client.post(
            "/chat",
            json={"query": "What is the weather in London?"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data

    @patch("app.agents.orchestrator.process_query", new_callable=AsyncMock)
    def test_chat_todo_query(self, mock_process, client: TestClient, auth_headers: dict):
        """POST /chat with a todo query should return a response."""
        mock_process.return_value = "Task 'Buy groceries' created successfully."
        resp = client.post(
            "/chat",
            json={"query": "Create a task: Buy groceries"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
