"""Authentication API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import controllers
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Request / Response schemas ──


class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str = ""


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str


class RegisterResponse(BaseModel):
    id: str
    username: str
    full_name: str
    message: str


# ── Endpoints ──


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and return a JWT access token.

    Accepts OAuth2 form-encoded username & password.
    Works with Swagger Authorize button. No client_id / client_secret needed.
    """
    result = controllers.login(db, form_data.username, form_data.password)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return result


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user. Returns the created user info (no token)."""
    result = controllers.register_user(
        db, request.username, request.password, request.full_name
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )
    return result
