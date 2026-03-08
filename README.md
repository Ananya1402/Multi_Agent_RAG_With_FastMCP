# Multi-Agent RAG System with FastMCP Integration

A **multi-agent AI system** built with **FastAPI** that answers FAQ queries using **Retrieval-Augmented Generation (RAG)**, provides **weather information**, and manages **tasks** through a **FastMCP Todo server**. The system uses **LangGraph** for agent orchestration, **ChromaDB** for vector storage, and is fully dockerized with a decoupled **Streamlit** frontend.

---

## Table of Contents

- [System Architecture](#system-architecture)
- [System Design](#system-design)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Docker Setup](#docker-setup)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Agents Deep Dive](#agents-deep-dive)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        STREAMLIT FRONTEND                          │
│                    (Decoupled Microservice)                         │
│            Chat UI │ Weather UI │ Todo Manager UI                   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │  HTTP/REST (JSON)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND                            │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌──────────────────┐  │
│  │ Auth API │  │ Chat API │  │Weather API│  │   Todo API       │  │
│  │ /auth/*  │  │ /chat    │  │ /weather  │  │   /todos/*       │  │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘  └────────┬─────────┘  │
│       │              │              │                  │            │
│       │         ┌────▼──────────────┴──────────────────┘            │
│       │         │                                                   │
│  JWT Auth   ┌───▼────────────────────────────────────┐             │
│  Middleware │    PARENT AGENT (LangGraph Orchestrator) │             │
│             │                                         │             │
│             │   ┌──────────┐  ┌─────────────────────┐│             │
│             │   │Intent    │  │  Conditional Router  ││             │
│             │   │Detection │──▶  faq → RAG Agent     ││             │
│             │   │(LLM)    │  │  weather → Tool Agent ││             │
│             │   └──────────┘  │  todo → Tool Agent   ││             │
│             │                 └─────────────────────┘│             │
│             └─────┬────────────────────┬─────────────┘             │
│                   │                    │                            │
│          ┌────────▼──────┐    ┌────────▼───────────┐               │
│          │   RAG AGENT   │    │    TOOL AGENT      │               │
│          │               │    │                    │               │
│          │ 1. Semantic   │    │  ┌──────────────┐  │               │
│          │    Search     │    │  │ Weather Tool │  │               │
│          │ 2. Context    │    │  │ (Open-Meteo) │  │               │
│          │    Building   │    │  └──────────────┘  │               │
│          │ 3. LLM Answer │    │  ┌──────────────┐  │               │
│          │    Generation │    │  │ Todo Tools   │  │               │
│          └───────┬───────┘    │  │ (FastMCP)    │  │               │
│                  │            │  └──────┬───────┘  │               │
│          ┌───────▼───────┐    └─────────┼──────────┘               │
│          │   ChromaDB    │              │                           │
│          │ Vector Store  │    ┌─────────▼──────────┐               │
│          │ (FAQ Data)    │    │  FastMCP Todo      │               │
│          └───────────────┘    │  Server (PostgreSQL)│              │
│                               └─────────┬──────────┘               │
│                                         │                          │
│                               ┌─────────▼──────────┐               │
│                               │   PostgreSQL DB    │               │
│                               │  (Users + Todos)   │               │
│                               └────────────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## System Design

### Microservices Architecture

The application follows a **microservices architecture** with two independently deployable services:

| Service         | Technology | Port | Responsibility                                  |
|----------------|-----------|------|------------------------------------------------|
| **Backend**     | FastAPI   | 8000 | API server, agent orchestration, RAG, MCP      |
| **Frontend**    | Streamlit | 8501 | User interface, communicates via REST API only  |
| **Database**    | PostgreSQL| 5432 | Persistent storage for users and todos          |

The frontend is **loosely coupled** — it only knows the backend's URL and communicates exclusively through HTTP REST calls. No shared code, no shared state.

### Multi-Agent System (LangGraph)

The agent system is built with **LangGraph**, implementing a directed state graph:

```
                    ┌─────────────────┐
                    │  detect_intent  │  (Entry Point)
                    │  (LLM-based)    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Conditional     │
                    │ Router          │
                    └──┬──────┬───┬───┘
                       │      │   │
            "faq"      │      │   │  "unknown"
                       │      │   │
              ┌────────▼┐  ┌──▼───▼─────┐  ┌───────────┐
              │rag_node │  │ tool_node  │  │unknown_node│
              │         │  │            │  │            │
              └────┬────┘  └─────┬──────┘  └─────┬──────┘
                   │             │               │
                   └─────────────┴───────────────┘
                                 │
                               [END]
```

1. **Parent Agent (Orchestrator)**: Receives queries, uses LLM to classify intent (`faq`, `weather`, `todo`, `unknown`), then routes to the appropriate specialist.
2. **RAG Agent**: Performs semantic search on ChromaDB, builds context from top-k results, and generates grounded answers using the LLM.
3. **Tool Agent**: Dispatches to weather API or FastMCP todo tools based on the classified intent.

### RAG Pipeline

```
CSV Data → LangChain Documents → OpenAI Embeddings → ChromaDB Vector Store
                                                            │
User Query → Embedding → Similarity Search (top-4) → Context Building → LLM → Answer
```

- **Data Source**: FAQ CSV file (386 question/answer pairs from BigRock)
- **Embeddings**: OpenAI `text-embedding-3-small`
- **Vector Store**: ChromaDB (in-memory + optional persist)
- **LLM**: GPT-4.1 Mini (configurable)
- **Fallback**: Returns "I couldn't find an answer" if no relevant context exists

### FastMCP Integration

The Todo service is implemented as a **FastMCP 3.x server** with tools exposed via the MCP protocol. Todos are persisted in **PostgreSQL** via SQLAlchemy:

- `create_task` — Create a new todo item
- `list_tasks` — List all tasks (with filter)
- `get_task` — Retrieve a task by ID
- `update_task` — Modify task title/description/status
- `delete_task` — Remove a task

The backend uses a **FastMCP Client** with in-memory transport (no network hop for MCP calls within the same process), while also exposing REST API endpoints for direct access. The agent also supports **keyword-based task resolution** — users can refer to tasks by name instead of ID.

### JWT Authentication

All API endpoints (except `/auth/*` and health checks) are protected by **JWT Bearer token authentication**.

Flow:
1. `POST /auth/register` or `POST /auth/login` → returns JWT
2. Include `Authorization: Bearer <token>` in subsequent requests
3. Token is validated on every protected endpoint

### Data Flow

```
User Input → Streamlit → POST /chat → JWT Validation → Orchestrator
  → Intent Detection (LLM) → Route to Agent → Execute → Return Response
  → Streamlit renders answer
```

---

## Tech Stack

| Component        | Technology                     |
|-----------------|-------------------------------|
| Backend API      | FastAPI, Uvicorn               |
| Agent Framework  | LangGraph, LangChain           |
| LLM              | OpenAI GPT-4.1 Mini            |
| Embeddings       | OpenAI text-embedding-3-small  |
| Vector Database  | ChromaDB                       |
| Database         | PostgreSQL, SQLAlchemy, Alembic|
| MCP Server       | FastMCP 3.x                    |
| Weather API      | Open-Meteo (free, no key)      |
| Authentication   | JWT (python-jose)              |
| Frontend         | Streamlit                      |
| HTTP Client      | httpx (async), requests         |
| Testing          | Pytest                         |
| Containerization | Docker, Docker Compose          |

---

## Project Structure

```
Multi_Agent_RAG_With_FastMCP/
├── docker-compose.yml          # Orchestrates backend + frontend containers
├── README.md
├── data/
│   ├── faqs.csv                # FAQ dataset (question/answer pairs)
│   └── faqs 3.xlsx             # Original Excel source
│
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── alembic.ini             # Alembic config (URL overridden by env.py)
│   ├── .env                    # Secret variables (gitignored)
│   ├── .env.example            # Template for env vars
│   ├── alembic/                # Database migrations
│   │   ├── env.py              # Migration environment (reads DATABASE_URL)
│   │   └── versions/           # Migration scripts
│   ├── app/
│   │   ├── main.py             # FastAPI entry point, CORS, lifespan
│   │   ├── config.py           # Settings from env vars
│   │   ├── database.py         # SQLAlchemy engine, session, Base
│   │   │
│   │   ├── models/             # ORM models
│   │   │   ├── __init__.py     # Exports User, Todo
│   │   │   ├── user.py         # User model
│   │   │   └── todo.py         # Todo model
│   │   │
│   │   ├── auth/               # Authentication module
│   │   │   ├── routes.py       # POST /auth/login, /auth/register
│   │   │   ├── controllers.py  # Login/register logic
│   │   │   └── jwt_handler.py  # JWT create/verify, FastAPI dependency
│   │   │
│   │   ├── chat/               # Chat module
│   │   │   ├── routes.py       # POST /chat
│   │   │   └── controllers.py  # Delegates to orchestrator
│   │   │
│   │   ├── weather/            # Weather module
│   │   │   ├── routes.py       # GET /weather
│   │   │   └── controllers.py  # Delegates to tool agent
│   │   │
│   │   ├── todo/               # Todo module
│   │   │   ├── routes.py       # CRUD /todos/*
│   │   │   └── controllers.py  # Proxies to FastMCP client
│   │   │
│   │   ├── agents/             # Multi-agent system
│   │   │   ├── orchestrator.py # Parent agent (LangGraph state graph)
│   │   │   ├── rag_agent.py    # RAG pipeline agent
│   │   │   └── tool_agent.py   # Weather + Todo agent
│   │   │
│   │   ├── rag/                # RAG infrastructure
│   │   │   ├── loader.py       # CSV → LangChain Documents
│   │   │   └── vectorstore.py  # ChromaDB build/query
│   │   │
│   │   └── mcp/                # FastMCP integration
│   │       ├── todo_server.py  # FastMCP server with CRUD tools (PostgreSQL)
│   │       └── client.py       # FastMCP client (in-memory transport)
│   │
│   └── tests/
│       ├── conftest.py         # Shared fixtures
│       ├── test_auth.py        # Auth API tests
│       ├── test_weather.py     # Weather API tests
│       ├── test_todos.py       # Todo API tests
│       └── test_chat.py        # Chat API tests
│
└── frontend/
    ├── Dockerfile
    ├── .dockerignore
    ├── requirements.txt
    ├── .env
    ├── .env.example
    ├── config.py               # Frontend configuration
    ├── api_client.py           # HTTP client for backend API
    ├── app.py                  # Streamlit application
    └── .streamlit/
        └── config.toml         # Streamlit server config
```

---

## Setup Instructions

### Prerequisites

- Python 3.12+
- OpenAI API key
- PostgreSQL 16+ (or use Docker which includes it)
- (Optional) Docker & Docker Compose

### Local Development (Without Docker)

#### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your OPENAI_API_KEY and DATABASE_URL

# Run database migrations
alembic upgrade head

# Run the backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API docs are available at **http://localhost:8000/docs** (Swagger UI).

#### 2. Frontend Setup

```bash
cd frontend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Run the frontend
streamlit run app.py --server.port 8501
```

The frontend is available at **http://localhost:8501**.

#### 3. Default Credentials

| Username | Password   |
|----------|-----------|
| admin    | admin123   |

You can also register a new account through the UI or API.

---

## Docker Setup

### Quick Start

```bash
# From the project root
cp backend/.env.example backend/.env
# Edit backend/.env with your OPENAI_API_KEY

docker-compose up --build
```

This starts three services:
- **PostgreSQL** at localhost:5432 (persistent via Docker volume)
- **Backend** at http://localhost:8000 (API + Swagger UI at `/docs`)
- **Frontend** at http://localhost:8501

The backend container automatically runs Alembic migrations on startup.

### Docker Networking

The `docker-compose.yml` overrides certain `.env` values for container networking:
- `DATABASE_URL` → points to `db:5432` instead of `localhost:5432`
- `BACKEND_URL` → frontend uses `http://backend:8000` internally
- `FAQ_CSV_PATH` → `/data/faqs.csv` (mounted from `./data`)

Your `.env` keeps `localhost` values so local development (without Docker) still works.

### Stop Services

```bash
docker-compose down
# To also remove volumes (clears DB and ChromaDB data):
docker-compose down -v
```

---

## API Documentation

Once the backend is running, interactive API docs are at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints Summary

| Method | Endpoint              | Auth | Tags           | Description                        |
|--------|-----------------------|------|----------------|------------------------------------|
| POST   | `/auth/login`         | No   | Authentication | Login and get JWT token            |
| POST   | `/auth/register`      | No   | Authentication | Register new user and get JWT      |
| POST   | `/chat`               | Yes  | Chat           | Send query to orchestrator agent   |
| GET    | `/weather`            | Yes  | Weather        | Get current weather for a city     |
| POST   | `/todos`              | Yes  | Todos          | Create a new task                  |
| GET    | `/todos`              | Yes  | Todos          | List all tasks                     |
| GET    | `/todos/{task_id}`    | Yes  | Todos          | Get a specific task                |
| PUT    | `/todos/{task_id}`    | Yes  | Todos          | Update a task                      |
| DELETE | `/todos/{task_id}`    | Yes  | Todos          | Delete a task                      |
| GET    | `/`                   | No   | Health         | Health check                       |
| GET    | `/health`             | No   | Health         | Detailed health check              |

### Example Usage

```bash
# 1. Login (uses form-encoded data for OAuth2 compatibility)
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d 'username=admin&password=admin123' \
  | jq -r '.access_token')

# 2. Chat (FAQ query)
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What domains are available from BigRock?"}'

# 3. Weather
curl -X GET "http://localhost:8000/weather?city=London" \
  -H "Authorization: Bearer $TOKEN"

# 4. Create a todo
curl -X POST http://localhost:8000/todos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy groceries", "description": "Milk, eggs, bread"}'
```

---

## Testing

Run the happy-path test suite:

```bash
cd backend
pytest tests/ -v
```

The test suite covers:
- **Auth API**: Registration, login, duplicate handling, JWT validation
- **Weather API**: Default city, custom city, auth enforcement
- **Todo API**: Create, list, update, delete tasks, auth enforcement
- **Chat API**: FAQ/weather/todo queries (mocked orchestrator for isolation)

---

## Agents Deep Dive

### Parent Agent (Orchestrator)

**File**: `backend/app/agents/orchestrator.py`

Uses LangGraph `StateGraph` with typed state (`AgentState`). The LLM classifies the user's intent into one of: `faq`, `weather`, `todo`, or `unknown`. A conditional edge routes to the appropriate specialist node based on the classification.

### RAG Agent

**File**: `backend/app/agents/rag_agent.py`

1. Receives the original query
2. Performs `similarity_search` against ChromaDB (top 4 results)
3. Formats retrieved documents into a context block
4. Sends context + query to GPT-4.1 Mini with strict grounding instructions
5. Returns the generated answer (or fallback message)

### Tool Agent

**File**: `backend/app/agents/tool_agent.py`

Dispatches to:
- **Weather Tool**: Calls the **Open-Meteo API** (free, no API key required). Uses a 2-step flow: geocode city name → fetch current weather.
- **Todo Tools**: Calls the **FastMCP Todo server** via in-memory MCP client. Supports keyword-based task resolution — users can refer to tasks by name/description instead of ID.

---

## Configuration Reference

All secrets and config are stored in `backend/.env`:

| Variable                          | Description                              | Default          |
|----------------------------------|------------------------------------------|------------------|
| `OPENAI_API_KEY`                 | OpenAI API key                           | (required)       |
| `OPENAI_MODEL`                   | LLM model name                           | `gpt-4.1-mini`   |
| `JWT_SECRET_KEY`                 | JWT signing secret                       | (required)       |
| `JWT_ALGORITHM`                  | JWT algorithm                            | `HS256`          |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`| Token expiry in minutes                  | `30`             |
| `DATABASE_URL`                   | PostgreSQL connection string             | (required)       |
| `WEATHER_DEFAULT_CITY`           | Default city for weather queries         | `London`         |
| `CHROMA_PERSIST_DIR`             | ChromaDB data directory                  | `./chroma_db`    |
| `CHROMA_COLLECTION_NAME`         | ChromaDB collection name                 | `faq_collection` |
| `FAQ_CSV_PATH`                   | Path to FAQ CSV file                     | `../data/faqs.csv`|

---

## License

See [LICENSE](LICENSE) for details.
