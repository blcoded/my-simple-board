import os

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "mini-kanban-secret-jwt-key-2026-super-secure")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 7

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "*",
]

# Database configuration
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "kanban.db"


def get_database_url() -> str:
    """Resolve and normalize database connection URL from environment variables.
    
    Supports DATABASE_URL or DB_URL environment variable, defaulting to SQLite.
    Automatically normalizes cloud provider legacy postgres:// URLs to postgresql://.
    """
    url = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
    if not url:
        return f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"

    url = url.strip()

    # Normalize Heroku / cloud legacy postgres:// URLs to standard SQLAlchemy postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    return url


DATABASE_URL = get_database_url()

