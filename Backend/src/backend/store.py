import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.auth import hash_password
from backend.database import Base, SessionLocal, create_db_engine
from backend.database import engine as default_engine
from backend.models import Priority, Task, TaskStatus, User

# Precompute demo hash once at module load to avoid repetitive slow bcrypt hashing on reset
DEMO_PASSWORD_HASH = hash_password("focus")


class DatabaseStore:
    def __init__(self, engine=None, session_factory=None) -> None:
        if engine is not None:
            self.engine = engine
        elif not hasattr(self, "engine"):
            self.engine = default_engine

        if session_factory is not None:
            self.session_factory = session_factory
        elif not hasattr(self, "session_factory"):
            self.session_factory = SessionLocal

        if not getattr(self, "_is_initialized", False):
            self.init_db()
            self._is_initialized = True
        else:
            self.reset_db()

    def configure(self, database_url: Optional[str] = None, engine=None) -> None:
        """Reconfigure the store with a new database URL or engine."""
        from sqlalchemy.orm import sessionmaker

        if engine is not None:
            self.engine = engine
        else:
            self.engine = create_db_engine(database_url)

        self.session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=self.engine,
        )
        self._is_initialized = False
        try:
            self.init_db()
            self._is_initialized = True
        except Exception as e:
            # Allow import to succeed if DB is starting; lifespan will retry
            print(f"Warning: Database initialization deferred at import time: {e}")

    def init_db(self, max_retries: int = 15, retry_delay: float = 2.0) -> None:
        """Initialize database tables with connection retries for container networks."""
        import time

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                Base.metadata.create_all(bind=self.engine)
                with self.session_factory() as session:
                    self._seed(session)
                self._is_initialized = True
                return
            except Exception as e:
                last_error = e
                err_msg = str(e).lower()
                is_transient = any(
                    x in err_msg
                    for x in [
                        "could not translate host name",
                        "temporary failure in name resolution",
                        "connection refused",
                        "operationalerror",
                        "the database system is starting up",
                        "server closed the connection unexpectedly",
                    ]
                )
                if is_transient and attempt < max_retries:
                    print(
                        f"Waiting for database connection (attempt {attempt}/{max_retries}): {e}. Retrying in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                else:
                    raise e

        if last_error:
            raise last_error

    def reset_db(self) -> None:
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        with self.session_factory() as session:
            self._seed(session)

    def reset(self) -> None:
        self.reset_db()


    def _seed(self, session: Session) -> None:
        demo_email = "ada@example.com"
        demo_user = session.get(User, demo_email)
        if not demo_user:
            demo_user = User(
                id=demo_email,
                email=demo_email,
                password_hash=DEMO_PASSWORD_HASH,
            )
            session.add(demo_user)
            session.flush()

        existing_tasks_count = session.scalar(
            select(func.count()).select_from(Task).where(Task.user_id == demo_user.id)
        )
        if existing_tasks_count == 0:
            seed_tasks = [
                Task(
                    id="task-onboarding",
                    user_id=demo_user.id,
                    title="Sketch onboarding flow",
                    description="Map the first three screens before writing any code.",
                    dueDate="2026-03-03",
                    priority=Priority.high,
                    status=TaskStatus.ideas,
                    position=0,
                ),
                Task(
                    id="task-tokens",
                    user_id=demo_user.id,
                    title="Audit color tokens",
                    description="Consolidate the 40 shades into a single scale.",
                    dueDate="2026-03-15",
                    priority=Priority.medium,
                    status=TaskStatus.ideas,
                    position=1,
                ),
                Task(
                    id="task-drag-physics",
                    user_id=demo_user.id,
                    title="Read on drag physics",
                    description="Two articles on easing curves for cards.",
                    dueDate="",
                    priority=Priority.low,
                    status=TaskStatus.ideas,
                    position=2,
                ),
                Task(
                    id="task-auth",
                    user_id=demo_user.id,
                    title="Build auth scaffold",
                    description="Routes, mock backend calls, session state.",
                    dueDate="2026-03-12",
                    priority=Priority.high,
                    status=TaskStatus.todo,
                    position=0,
                ),
                Task(
                    id="task-dnd",
                    user_id=demo_user.id,
                    title="Wire drag-and-drop",
                    description="Reorder within a column plus cross-lane moves.",
                    dueDate="2026-03-14",
                    priority=Priority.medium,
                    status=TaskStatus.todo,
                    position=1,
                ),
                Task(
                    id="task-empty-states",
                    user_id=demo_user.id,
                    title="Trim copy in empty states",
                    description="Keep each under nine words.",
                    dueDate="",
                    priority=Priority.low,
                    status=TaskStatus.todo,
                    position=2,
                ),
                Task(
                    id="task-card",
                    user_id=demo_user.id,
                    title="Design the task card",
                    description="Finalize priority chips and due-date states.",
                    dueDate="2026-03-10",
                    priority=Priority.high,
                    status=TaskStatus.progress,
                    position=0,
                ),
                Task(
                    id="task-api",
                    user_id=demo_user.id,
                    title="Set up mock API",
                    description="Stubbed endpoints for tasks and auth.",
                    dueDate="2026-03-09",
                    priority=Priority.medium,
                    status=TaskStatus.done,
                    position=0,
                    completedAt="2026-03-09T10:00:00.000Z",
                ),
                Task(
                    id="task-type",
                    user_id=demo_user.id,
                    title="Pick type pairing",
                    description="Space Grotesk for display, Inter for body.",
                    dueDate="2026-03-08",
                    priority=Priority.low,
                    status=TaskStatus.done,
                    position=1,
                    completedAt="2026-03-08T10:00:00.000Z",
                ),
            ]
            session.add_all(seed_tasks)
        session.commit()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        with self.session_factory() as session:
            return session.get(User, user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        with self.session_factory() as session:
            norm_email = email.strip().lower()
            return session.scalar(select(User).where(User.email == norm_email))

    def create_user(self, email: str, password_hash: str) -> User:
        with self.session_factory() as session:
            norm_email = email.strip().lower()
            user = User(
                id=norm_email,
                email=norm_email,
                password_hash=password_hash,
            )
            session.add(user)
            session.commit()
            return user

    def _normalize_positions(self, session: Session, user_id: str) -> None:
        for col in TaskStatus:
            col_tasks = list(
                session.scalars(
                    select(Task)
                    .where(Task.user_id == user_id, Task.status == col)
                    .order_by(Task.position, Task.id)
                ).all()
            )
            for idx, t in enumerate(col_tasks):
                if t.position != idx:
                    t.position = idx
        session.flush()

    def get_tasks(self, user_id: str) -> List[Task]:
        with self.session_factory() as session:
            self._normalize_positions(session, user_id)
            session.commit()
            tasks = list(
                session.scalars(
                    select(Task).where(Task.user_id == user_id)
                ).all()
            )
            tasks.sort(key=lambda x: (x.status.value, x.position))
            return tasks

    def get_task(self, user_id: str, task_id: str) -> Optional[Task]:
        with self.session_factory() as session:
            return session.scalar(
                select(Task).where(Task.user_id == user_id, Task.id == task_id)
            )

    def create_task(
        self,
        user_id: str,
        title: str,
        description: str,
        due_date: str,
        priority: Priority,
        status: TaskStatus,
    ) -> Task:
        with self.session_factory() as session:
            col_tasks = list(
                session.scalars(
                    select(Task)
                    .where(Task.user_id == user_id, Task.status == status)
                    .order_by(Task.position)
                ).all()
            )
            position = len(col_tasks)

            now_iso = datetime.now(timezone.utc).isoformat()
            completed_at = now_iso if status == TaskStatus.done else None

            base_id = f"task-{int(time.time() * 1000)}"
            task_id = base_id
            counter = 1
            while session.get(Task, task_id) is not None:
                task_id = f"{base_id}-{counter}"
                counter += 1

            task = Task(
                id=task_id,
                user_id=user_id,
                title=title.strip(),
                description=description.strip(),
                dueDate=due_date,
                priority=priority,
                status=status,
                position=position,
                completedAt=completed_at,
            )
            session.add(task)
            session.flush()
            self._normalize_positions(session, user_id)
            session.commit()
            return task

    def update_task(
        self,
        user_id: str,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: Optional[Priority] = None,
        status: Optional[TaskStatus] = None,
    ) -> Optional[Task]:
        with self.session_factory() as session:
            task = session.scalar(
                select(Task).where(Task.user_id == user_id, Task.id == task_id)
            )
            if not task:
                return None

            if title is not None:
                task.title = title.strip()
            if description is not None:
                task.description = description.strip()
            if due_date is not None:
                task.dueDate = due_date
            if priority is not None:
                task.priority = priority

            if status is not None and status != task.status:
                old_status = task.status
                task.status = status
                if status == TaskStatus.done and old_status != TaskStatus.done:
                    task.completedAt = datetime.now(timezone.utc).isoformat()
                elif status != TaskStatus.done:
                    task.completedAt = None

                dest_tasks = list(
                    session.scalars(
                        select(Task)
                        .where(Task.user_id == user_id, Task.status == status, Task.id != task_id)
                        .order_by(Task.position)
                    ).all()
                )
                task.position = len(dest_tasks)
                session.flush()
                self._normalize_positions(session, user_id)

            session.commit()
            return task

    def move_task(
        self,
        user_id: str,
        task_id: str,
        status: TaskStatus,
        target_id: Optional[str] = None,
        position: Optional[int] = None,
    ) -> Optional[List[Task]]:
        with self.session_factory() as session:
            moving_task = session.scalar(
                select(Task).where(Task.user_id == user_id, Task.id == task_id)
            )
            if not moving_task:
                return None

            old_status = moving_task.status

            # Separate destination column tasks and other tasks
            dest_tasks = list(
                session.scalars(
                    select(Task)
                    .where(Task.user_id == user_id, Task.status == status, Task.id != task_id)
                    .order_by(Task.position)
                ).all()
            )

            insert_index = len(dest_tasks)
            if target_id:
                for idx, t in enumerate(dest_tasks):
                    if t.id == target_id:
                        insert_index = idx
                        break
            elif position is not None:
                insert_index = max(0, min(position, len(dest_tasks)))

            moving_task.status = status
            if status == TaskStatus.done:
                if not moving_task.completedAt:
                    moving_task.completedAt = datetime.now(timezone.utc).isoformat()
            else:
                moving_task.completedAt = None

            dest_tasks.insert(insert_index, moving_task)
            for idx, t in enumerate(dest_tasks):
                t.position = idx

            # Re-index old column if column changed
            if old_status != status:
                old_col_tasks = list(
                    session.scalars(
                        select(Task)
                        .where(Task.user_id == user_id, Task.status == old_status, Task.id != task_id)
                        .order_by(Task.position)
                    ).all()
                )
                for idx, t in enumerate(old_col_tasks):
                    t.position = idx

            session.flush()
            self._normalize_positions(session, user_id)
            session.commit()

            tasks = list(
                session.scalars(
                    select(Task).where(Task.user_id == user_id)
                ).all()
            )
            tasks.sort(key=lambda x: (x.status.value, x.position))
            return tasks

    def delete_task(self, user_id: str, task_id: str) -> bool:
        with self.session_factory() as session:
            task = session.scalar(
                select(Task).where(Task.user_id == user_id, Task.id == task_id)
            )
            if not task:
                return False
            session.delete(task)
            session.flush()
            self._normalize_positions(session, user_id)
            session.commit()
            return True

    def clear_completed(self, user_id: str) -> int:
        with self.session_factory() as session:
            done_tasks = list(
                session.scalars(
                    select(Task).where(Task.user_id == user_id, Task.status == TaskStatus.done)
                ).all()
            )
            count = len(done_tasks)
            for t in done_tasks:
                session.delete(t)
            session.flush()
            self._normalize_positions(session, user_id)
            session.commit()
            return count


SQLAlchemyStore = DatabaseStore
InMemoryStore = DatabaseStore
store = DatabaseStore()
