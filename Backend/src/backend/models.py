from enum import Enum
from typing import List, Optional
from sqlalchemy import ForeignKey, Integer, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class TaskStatus(str, Enum):
    ideas = "ideas"
    todo = "todo"
    progress = "progress"
    done = "done"


class Priority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Task.position",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<User id={self.id!r} email={self.email!r}>"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, default="", nullable=False)
    dueDate: Mapped[str] = mapped_column("dueDate", String, default="", nullable=False)
    priority: Mapped[Priority] = mapped_column(
        SQLEnum(Priority, native_enum=False, values_callable=lambda obj: [e.value for e in obj]),
        default=Priority.medium,
        nullable=False,
    )
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus, native_enum=False, values_callable=lambda obj: [e.value for e in obj]),
        default=TaskStatus.ideas,
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completedAt: Mapped[Optional[str]] = mapped_column(
        "completedAt", String, nullable=True, default=None
    )

    user: Mapped[Optional[User]] = relationship("User", back_populates="tasks")

    def __init__(self, **kwargs):
        kwargs.setdefault("description", "")
        kwargs.setdefault("dueDate", "")
        kwargs.setdefault("priority", Priority.medium)
        kwargs.setdefault("status", TaskStatus.ideas)
        kwargs.setdefault("position", 0)
        kwargs.setdefault("completedAt", None)
        if isinstance(kwargs.get("priority"), str):
            kwargs["priority"] = Priority(kwargs["priority"])
        if isinstance(kwargs.get("status"), str):
            kwargs["status"] = TaskStatus(kwargs["status"])
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return (
            f"<Task id={self.id!r} title={self.title!r} "
            f"status={self.status!r} position={self.position}>"
        )
