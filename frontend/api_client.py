"""API client – handles all HTTP communication with the FastAPI backend."""

import requests
from config import BACKEND_URL


class APIClient:
    """Stateless HTTP client for the backend API."""

    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url.rstrip("/")
        self.token: str | None = None

    @property
    def _auth_headers(self) -> dict:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    # ── Auth ──

    def login(self, username: str, password: str) -> dict:
        resp = requests.post(
            f"{self.base_url}/auth/login",
            data={"username": username, "password": password},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        self.token = data["access_token"]
        return data

    def register(self, username: str, password: str, full_name: str = "") -> dict:
        resp = requests.post(
            f"{self.base_url}/auth/register",
            json={
                "username": username,
                "password": password,
                "full_name": full_name,
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    # ── Chat ──

    def chat(self, query: str) -> dict:
        resp = requests.post(
            f"{self.base_url}/chat",
            json={"query": query},
            headers=self._auth_headers,
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()

    # ── Weather ──

    def get_weather(self, city: str | None = None) -> dict:
        params = {}
        if city:
            params["city"] = city
        resp = requests.get(
            f"{self.base_url}/weather",
            params=params,
            headers=self._auth_headers,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    # ── Todos ──

    def create_task(self, title: str, description: str = "") -> dict:
        resp = requests.post(
            f"{self.base_url}/todos",
            json={"title": title, "description": description},
            headers=self._auth_headers,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def list_tasks(self, include_completed: bool = True) -> list:
        resp = requests.get(
            f"{self.base_url}/todos",
            params={"include_completed": include_completed},
            headers=self._auth_headers,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def get_task(self, task_id: str) -> dict:
        resp = requests.get(
            f"{self.base_url}/todos/{task_id}",
            headers=self._auth_headers,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def update_task(self, task_id: str, **kwargs) -> dict:
        resp = requests.put(
            f"{self.base_url}/todos/{task_id}",
            json=kwargs,
            headers=self._auth_headers,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def delete_task(self, task_id: str) -> dict:
        resp = requests.delete(
            f"{self.base_url}/todos/{task_id}",
            headers=self._auth_headers,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    # ── Health ──

    def health(self) -> dict:
        resp = requests.get(f"{self.base_url}/health", timeout=5)
        resp.raise_for_status()
        return resp.json()
