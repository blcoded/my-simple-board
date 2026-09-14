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
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")

