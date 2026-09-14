from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TaskStatus(str, Enum):
    ideas = "ideas"
    todo = "todo"
    progress = "progress"
    done = "done"


class Priority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


@dataclass
class User:
    id: str
    email: str
    password_hash: str


@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    dueDate: str = ""
    priority: Priority = Priority.medium
    status: TaskStatus = TaskStatus.ideas
    position: int = 0
    completedAt: Optional[str] = None
