"""Database Migration Script: SQLite to PostgreSQL

Copies all users and tasks from SQLite (kanban.db) to a target PostgreSQL database.
Preserves user IDs, password hashes, task attributes, ordering, and completion dates.

Usage:
    uv run python scripts/migrate_to_postgres.py --target "postgresql://user:pass@host:5432/dbname"
    
    Or set the TARGET_DATABASE_URL or DATABASE_URL environment variable:
    set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/kanban_db
    uv run python scripts/migrate_to_postgres.py
"""

import argparse
import os
import sys
from pathlib import Path

# Add src to sys.path so backend modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import DEFAULT_DB_PATH
from backend.database import Base, create_db_engine
from backend.models import Task, User


def normalize_url(url: str) -> str:
    url = url.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def migrate(source_url: str, target_url: str, dry_run: bool = False):
    source_url = normalize_url(source_url)
    target_url = normalize_url(target_url)

    print(f"Connecting to source database: {source_url}")
    source_engine = create_db_engine(source_url)

    print(f"Connecting to target database: {target_url}")
    target_engine = create_db_engine(target_url)

    # Verify target connection
    try:
        with target_engine.connect() as conn:
            print("Successfully connected to target PostgreSQL database.")
    except Exception as e:
        print(f"Error connecting to target database: {e}", file=sys.stderr)
        sys.exit(1)

    # Ensure tables exist in target
    print("Ensuring target schema tables (users, tasks) exist...")
    Base.metadata.create_all(bind=target_engine)

    with Session(source_engine) as src_session, Session(target_engine) as tgt_session:
        # 1. Fetch source users
        source_users = src_session.scalars(select(User)).all()
        print(f"Found {len(source_users)} user(s) in source database.")

        users_migrated = 0
        users_skipped = 0
        for u in source_users:
            existing = tgt_session.get(User, u.id)
            if existing:
                users_skipped += 1
                continue
            if not dry_run:
                tgt_session.add(
                    User(
                        id=u.id,
                        email=u.email,
                        password_hash=u.password_hash,
                    )
                )
            users_migrated += 1

        if not dry_run:
            tgt_session.flush()

        # 2. Fetch source tasks
        source_tasks = src_session.scalars(select(Task)).all()
        print(f"Found {len(source_tasks)} task(s) in source database.")

        tasks_migrated = 0
        tasks_skipped = 0
        for t in source_tasks:
            existing = tgt_session.get(Task, t.id)
            if existing:
                tasks_skipped += 1
                continue
            if not dry_run:
                tgt_session.add(
                    Task(
                        id=t.id,
                        user_id=t.user_id,
                        title=t.title,
                        description=t.description,
                        dueDate=t.dueDate,
                        priority=t.priority,
                        status=t.status,
                        position=t.position,
                        completedAt=t.completedAt,
                    )
                )
            tasks_migrated += 1

        if not dry_run:
            tgt_session.commit()
            print("\nMigration completed successfully!")
        else:
            print("\n[Dry Run] No changes committed.")

        print(f"  Users: {users_migrated} migrated, {users_skipped} already existed.")
        print(f"  Tasks: {tasks_migrated} migrated, {tasks_skipped} already existed.")


def main():
    default_sqlite = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"
    default_target = os.getenv("TARGET_DATABASE_URL") or os.getenv("DATABASE_URL")

    parser = argparse.ArgumentParser(description="Migrate Mini Kanban DB from SQLite to PostgreSQL")
    parser.add_argument(
        "--source",
        default=default_sqlite,
        help=f"Source database URL (default: {default_sqlite})",
    )
    parser.add_argument(
        "--target",
        default=default_target,
        help="Target PostgreSQL database URL (e.g. postgresql://user:pass@localhost:5432/kanban_db)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the migration without writing changes to target",
    )

    args = parser.parse_args()

    if not args.target or args.target.startswith("sqlite"):
        print(
            "Error: A valid target PostgreSQL database URL must be provided via --target or DATABASE_URL.\n"
            "Example: --target postgresql://postgres:postgres@localhost:5432/kanban_db",
            file=sys.stderr,
        )
        sys.exit(1)

    migrate(args.source, args.target, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
