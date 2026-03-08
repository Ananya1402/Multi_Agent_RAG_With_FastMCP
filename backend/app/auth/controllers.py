"""Authentication controller – handles login and registration via PostgreSQL."""

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.auth.jwt_handler import create_access_token
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """Validate credentials and return User ORM object or None."""
    user = db.query(User).filter(User.username == username).first()
    if user and pwd_context.verify(password, user.hashed_password):
        return user
    return None


def login(db: Session, username: str, password: str) -> dict | None:
    """Authenticate user and return JWT tokens."""
    user = authenticate_user(db, username, password)
    if not user:
        return None
    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
    }


def register_user(
    db: Session, username: str, password: str, full_name: str = ""
) -> dict | None:
    """Register a new user. Returns user info or None if username exists."""
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return None

    hashed = pwd_context.hash(password)
    user = User(
        username=username,
        hashed_password=hashed,
        full_name=full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": str(user.id),
        "username": user.username,
        "full_name": user.full_name,
        "message": "User registered successfully",
    }
