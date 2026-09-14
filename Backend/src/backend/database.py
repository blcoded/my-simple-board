import os
from typing import Any, Dict, Generator, Optional
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.config import get_database_url


class Base(DeclarativeBase):
    pass


def get_engine_options(database_url: str) -> Dict[str, Any]:
    """Build database-agnostic engine options based on connection dialect."""
    connect_args: Dict[str, Any] = {}
    engine_kwargs: Dict[str, Any] = {}

    is_sqlite = database_url.startswith("sqlite")

    if is_sqlite:
        connect_args["check_same_thread"] = False
        if ":memory:" in database_url:
            engine_kwargs["poolclass"] = StaticPool
    else:
        # Generic production RDBMS settings (e.g. PostgreSQL, MySQL)
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = int(os.getenv("DB_POOL_RECYCLE", "300"))

    if connect_args:
        engine_kwargs["connect_args"] = connect_args

    return engine_kwargs


def create_db_engine(database_url: Optional[str] = None) -> Engine:
    """Create a SQLAlchemy Engine with database-agnostic configuration."""
    url = database_url or get_database_url()
    engine_kwargs = get_engine_options(url)
    eng = create_engine(url, **engine_kwargs)

    # Attach SQLite-specific PRAGMAs only when using SQLite
    if url.startswith("sqlite"):
        @event.listens_for(eng, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            try:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
            except Exception:
                pass

    return eng


engine = create_db_engine()
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
