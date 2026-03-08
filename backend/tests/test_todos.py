"""Happy-path tests for the Todo API (FastMCP-backed)."""

from fastapi.testclient import TestClient


class TestTodoAPI:
    """Todo CRUD endpoint tests."""

    def test_create_task(self, client: TestClient, auth_headers: dict):
        """POST /todos should create a task and return it."""
        resp = client.post(
            "/todos",
            json={"title": "Test Task", "description": "A test task"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Test Task"
        assert data["description"] == "A test task"
        assert data["completed"] is False
        assert "id" in data

    def test_list_tasks(self, client: TestClient, auth_headers: dict):
        """GET /todos should return a list of tasks."""
        # Create one first
        client.post(
            "/todos",
            json={"title": "List Test"},
            headers=auth_headers,
        )
        resp = client.get("/todos", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_update_task(self, client: TestClient, auth_headers: dict):
        """PUT /todos/{id} should update a task."""
        # Create
        create_resp = client.post(
            "/todos",
            json={"title": "Update Me"},
            headers=auth_headers,
        )
        task_id = create_resp.json()["id"]

        # Update
        resp = client.put(
            f"/todos/{task_id}",
            json={"title": "Updated Title", "completed": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Updated Title"
        assert data["completed"] is True

    def test_delete_task(self, client: TestClient, auth_headers: dict):
        """DELETE /todos/{id} should delete the task."""
        # Create
        create_resp = client.post(
            "/todos",
            json={"title": "Delete Me"},
            headers=auth_headers,
        )
        task_id = create_resp.json()["id"]

        # Delete
        resp = client.delete(f"/todos/{task_id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] is True

    def test_todo_requires_auth(self, client: TestClient):
        """Todo endpoints should require JWT."""
        resp = client.get("/todos")
        assert resp.status_code == 401
