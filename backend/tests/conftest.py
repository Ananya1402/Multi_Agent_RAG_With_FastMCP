"""Shared test fixtures and helpers."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """Create a FastAPI TestClient for integration testing."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth_headers(client: TestClient) -> dict:
    """Register a test user, then login to obtain Authorization headers."""
    # Register (may already exist if tests ran before)
    client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "password": "testpass123",
            "full_name": "Test User",
        },
    )
    # Login to get the token
    resp = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "testpass123"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
