"""Happy-path tests for the Authentication API."""

from fastapi.testclient import TestClient


class TestAuthAPI:
    """Authentication endpoint tests."""

    def test_health_endpoint(self, client: TestClient):
        """GET / should return running status."""
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "running"

    def test_health_detailed(self, client: TestClient):
        """GET /health should return healthy status."""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_register_new_user(self, client: TestClient):
        """POST /auth/register should create a user (no token in response)."""
        resp = client.post(
            "/auth/register",
            json={
                "username": "newuser_auth",
                "password": "password123",
                "full_name": "New User",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["username"] == "newuser_auth"
        assert data["message"] == "User registered successfully"
        assert "access_token" not in data

    def test_register_duplicate_user(self, client: TestClient):
        """Duplicate registration should return 409."""
        # Register once
        client.post(
            "/auth/register",
            json={"username": "dupuser", "password": "pass123"},
        )
        # Try again
        resp = client.post(
            "/auth/register",
            json={"username": "dupuser", "password": "pass123"},
        )
        assert resp.status_code == 409

    def test_login_success(self, client: TestClient):
        """Login with valid credentials should return JWT."""
        # Ensure user exists
        client.post(
            "/auth/register",
            json={"username": "loginuser", "password": "pass123"},
        )
        resp = client.post(
            "/auth/login",
            data={"username": "loginuser", "password": "pass123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

    def test_login_invalid_credentials(self, client: TestClient):
        """Login with wrong password should return 401."""
        resp = client.post(
            "/auth/login",
            data={"username": "admin", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    def test_protected_endpoint_without_token(self, client: TestClient):
        """Accessing a protected endpoint without JWT should return 401."""
        resp = client.get("/weather")
        assert resp.status_code == 401
