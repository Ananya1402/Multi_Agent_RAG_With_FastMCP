"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.auth.routes import router as auth_router
from app.chat.routes import router as chat_router
from app.weather.routes import router as weather_router
from app.todo.routes import router as todo_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle events."""
    logger.info("Starting Multi-Agent RAG System...")

    # Create database tables (Alembic manages migrations, this is a safety net)
    from app.database import engine, Base
    from app.models import User, Todo  # noqa: F401 – register models
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")

    # Seed default admin user (if not exists)
    from app.database import SessionLocal
    from app.auth.controllers import pwd_context
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(
                username="admin",
                hashed_password=pwd_context.hash("admin123"),
                full_name="Admin User",
            ))
            db.commit()
            logger.info("Default admin user created.")
    finally:
        db.close()

    # Pre-build the vector store on startup
    try:
        from app.rag.vectorstore import build_vectorstore
        build_vectorstore()
        logger.info("Vector store ready.")
    except Exception as e:
        logger.error("Failed to build vector store: %s", e)

    yield

    logger.info("Shutting down Multi-Agent RAG System.")


app = FastAPI(
    title="Multi-Agent RAG System with FastMCP",
    description=(
        "A multi-agent AI system that answers FAQ queries using RAG, "
        "provides weather information, and manages tasks through a "
        "FastMCP Todo server. All APIs are protected by JWT authentication."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS – allow the Streamlit frontend (and any other origins in dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ──
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(weather_router)
app.include_router(todo_router)


@app.get("/", tags=["Health"])
def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Multi-Agent RAG System with FastMCP",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "model": settings.OPENAI_MODEL,
        "default_city": settings.WEATHER_DEFAULT_CITY,
    }
