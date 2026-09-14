import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from backend.auth import hash_password
from backend.database import Base, create_db_engine, get_db
from backend.models import Priority, Task, TaskStatus, User
from backend.store import DatabaseStore


def test_sqlite_file_persistence():
    """Verify data is persisted to a SQLite database file and readable by a new store instance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_persistence.db"
        db_url = f"sqlite:///{db_path.as_posix()}"

        engine1 = create_db_engine(db_url)
        session_factory1 = sessionmaker(
            autocommit=False, autoflush=False, expire_on_commit=False, bind=engine1
        )
        store1 = DatabaseStore(engine=engine1, session_factory=session_factory1)

        # Create user and custom task
        user = store1.create_user("persist@example.com", hash_password("secret123"))
        task = store1.create_task(
            user_id=user.id,
            title="Persisted SQLite Task",
            description="Testing disk persistence across restarts",
            due_date="2026-05-01",
            priority=Priority.high,
            status=TaskStatus.todo,
        )
        assert task.title == "Persisted SQLite Task"

        # Dispose engine1 to simulate app shutdown
        engine1.dispose()

        # Re-open the database with a second engine and store instance
        engine2 = create_db_engine(db_url)
        session_factory2 = sessionmaker(
            autocommit=False, autoflush=False, expire_on_commit=False, bind=engine2
        )
        store2 = DatabaseStore(engine=engine2, session_factory=session_factory2)

        persisted_user = store2.get_user_by_email("persist@example.com")
        assert persisted_user is not None
        assert persisted_user.id == "persist@example.com"

        user_tasks = store2.get_tasks(persisted_user.id)
        assert len(user_tasks) == 1
        assert user_tasks[0].id == task.id
        assert user_tasks[0].title == "Persisted SQLite Task"
        assert user_tasks[0].description == "Testing disk persistence across restarts"
        assert user_tasks[0].dueDate == "2026-05-01"
        assert user_tasks[0].priority == Priority.high
        assert user_tasks[0].status == TaskStatus.todo

        engine2.dispose()


def test_cascade_delete_user_removes_tasks():
    """Verify foreign key ON DELETE CASCADE removes associated tasks when a user is deleted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_cascade.db"
        db_url = f"sqlite:///{db_path.as_posix()}"

        engine = create_db_engine(db_url)
        session_factory = sessionmaker(
            autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
        )
        store = DatabaseStore(engine=engine, session_factory=session_factory)

        user = store.create_user("cascade@example.com", hash_password("pass"))
        t1 = store.create_task(user.id, "Task 1", "", "", Priority.low, TaskStatus.ideas)
        t2 = store.create_task(user.id, "Task 2", "", "", Priority.low, TaskStatus.todo)

        with session_factory() as s:
            tasks_before = s.scalars(select(Task).where(Task.user_id == user.id)).all()
            assert len(tasks_before) == 2

            # Delete the user directly via SQL / ORM
            user_obj = s.get(User, user.id)
            s.delete(user_obj)
            s.commit()

            tasks_after = s.scalars(select(Task).where(Task.user_id == user.id)).all()
            assert len(tasks_after) == 0

        engine.dispose()


def test_unique_email_constraint():
    """Verify SQLite enforces unique email constraint on the users table."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_unique.db"
        db_url = f"sqlite:///{db_path.as_posix()}"

        engine = create_db_engine(db_url)
        session_factory = sessionmaker(
            autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
        )
        store = DatabaseStore(engine=engine, session_factory=session_factory)

        store.create_user("unique@example.com", hash_password("pass1"))

        with pytest.raises(IntegrityError):
            with session_factory() as s:
                duplicate_user = User(
                    id="different-id",
                    email="unique@example.com",
                    password_hash=hash_password("pass2"),
                )
                s.add(duplicate_user)
                s.commit()

        engine.dispose()


def test_get_db_generator():
    """Verify get_db dependency yields an active session and closes it on generator exit."""
    gen = get_db()
    session = next(gen)
    res = session.scalar(select(1))
    assert res == 1
    with pytest.raises(StopIteration):
        next(gen)


def test_database_url_env_resolution(monkeypatch):
    """Verify get_database_url resolves DATABASE_URL and DB_URL environment variables."""
    from backend.config import get_database_url

    # 1. Standard DATABASE_URL
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:secret@localhost:5432/kanban")
    assert get_database_url() == "postgresql://user:secret@localhost:5432/kanban"

    # 2. Legacy Heroku postgres:// prefix normalization
    monkeypatch.setenv("DATABASE_URL", "postgres://user:secret@localhost:5432/kanban")
    assert get_database_url() == "postgresql://user:secret@localhost:5432/kanban"

    # 3. Fallback to DB_URL if DATABASE_URL is not set
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_URL", "mysql://user:secret@localhost:3306/kanban")
    assert get_database_url() == "mysql://user:secret@localhost:3306/kanban"


def test_database_agnostic_engine_options():
    """Verify engine options are tailored per database dialect (e.g. SQLite vs PostgreSQL)."""
    from backend.database import get_engine_options

    # SQLite options
    sqlite_opts = get_engine_options("sqlite:///path/to/test.db")
    assert sqlite_opts["connect_args"]["check_same_thread"] is False
    assert "pool_pre_ping" not in sqlite_opts

    # SQLite in-memory options
    mem_opts = get_engine_options("sqlite:///:memory:")
    assert "poolclass" in mem_opts

    # PostgreSQL / other database options
    pg_opts = get_engine_options("postgresql://user:pass@localhost:5432/mydb")
    assert "connect_args" not in pg_opts
    assert pg_opts["pool_pre_ping"] is True
    assert pg_opts["pool_recycle"] == 300


def test_store_dynamic_configuration():
    """Verify store can be reconfigured dynamically with a new database URL."""
    test_store = DatabaseStore()
    test_store.configure("sqlite:///:memory:")
    assert "sqlite" in str(test_store.engine.url)
    assert len(test_store.get_tasks("ada@example.com")) == 9


