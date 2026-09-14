import copy
import threading
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.auth import hash_password
from backend.models import Priority, Task, TaskStatus, User


# Precompute demo hash once at module load to avoid repetitive slow bcrypt hashing on reset
DEMO_PASSWORD_HASH = hash_password("focus")


class InMemoryStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.users: Dict[str, User] = {}
        self.users_by_email: Dict[str, User] = {}
        self.tasks_by_user: Dict[str, List[Task]] = {}
        self._seed()

    def _seed(self) -> None:
        demo_email = "ada@example.com"
        demo_user = User(
            id=demo_email,
            email=demo_email,
            password_hash=DEMO_PASSWORD_HASH,
        )
        self.users[demo_user.id] = demo_user
        self.users_by_email[demo_email] = demo_user

        seed_tasks = [
            Task(
                id="task-onboarding",
                title="Sketch onboarding flow",
                description="Map the first three screens before writing any code.",
                dueDate="2026-03-03",
                priority=Priority.high,
                status=TaskStatus.ideas,
                position=0,
            ),
            Task(
                id="task-tokens",
                title="Audit color tokens",
                description="Consolidate the 40 shades into a single scale.",
                dueDate="2026-03-15",
                priority=Priority.medium,
                status=TaskStatus.ideas,
                position=1,
            ),
            Task(
                id="task-drag-physics",
                title="Read on drag physics",
                description="Two articles on easing curves for cards.",
                dueDate="",
                priority=Priority.low,
                status=TaskStatus.ideas,
                position=2,
            ),
            Task(
                id="task-auth",
                title="Build auth scaffold",
                description="Routes, mock backend calls, session state.",
                dueDate="2026-03-12",
                priority=Priority.high,
                status=TaskStatus.todo,
                position=0,
            ),
            Task(
                id="task-dnd",
                title="Wire drag-and-drop",
                description="Reorder within a column plus cross-lane moves.",
                dueDate="2026-03-14",
                priority=Priority.medium,
                status=TaskStatus.todo,
                position=1,
            ),
            Task(
                id="task-empty-states",
                title="Trim copy in empty states",
                description="Keep each under nine words.",
                dueDate="",
                priority=Priority.low,
                status=TaskStatus.todo,
                position=2,
            ),
            Task(
                id="task-card",
                title="Design the task card",
                description="Finalize priority chips and due-date states.",
                dueDate="2026-03-10",
                priority=Priority.high,
                status=TaskStatus.progress,
                position=0,
            ),
            Task(
                id="task-api",
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
                title="Pick type pairing",
                description="Space Grotesk for display, Inter for body.",
                dueDate="2026-03-08",
                priority=Priority.low,
                status=TaskStatus.done,
                position=1,
                completedAt="2026-03-08T10:00:00.000Z",
            ),
        ]
        self.tasks_by_user[demo_user.id] = seed_tasks

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        with self._lock:
            return self.users.get(user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        with self._lock:
            return self.users_by_email.get(email.strip().lower())

    def create_user(self, email: str, password_hash: str) -> User:
        with self._lock:
            norm_email = email.strip().lower()
            user = User(
                id=norm_email,
                email=norm_email,
                password_hash=password_hash,
            )
            self.users[user.id] = user
            self.users_by_email[norm_email] = user
            self.tasks_by_user[user.id] = []
            return user

    def _normalize_positions_locked(self, user_id: str) -> None:
        tasks = self.tasks_by_user.get(user_id, [])
        for col in TaskStatus:
            col_tasks = [t for t in tasks if t.status == col]
            col_tasks.sort(key=lambda t: t.position)
            for idx, t in enumerate(col_tasks):
                t.position = idx

    def get_tasks(self, user_id: str) -> List[Task]:
        with self._lock:
            tasks = self.tasks_by_user.get(user_id, [])
            self._normalize_positions_locked(user_id)
            return [copy.deepcopy(t) for t in sorted(tasks, key=lambda x: (x.status.value, x.position))]

    def get_task(self, user_id: str, task_id: str) -> Optional[Task]:
        with self._lock:
            tasks = self.tasks_by_user.get(user_id, [])
            for t in tasks:
                if t.id == task_id:
                    return copy.deepcopy(t)
            return None

    def create_task(
        self,
        user_id: str,
        title: str,
        description: str,
        due_date: str,
        priority: Priority,
        status: TaskStatus,
    ) -> Task:
        with self._lock:
            if user_id not in self.tasks_by_user:
                self.tasks_by_user[user_id] = []

            tasks = self.tasks_by_user[user_id]
            col_tasks = [t for t in tasks if t.status == status]
            position = len(col_tasks)

            now_iso = datetime.now(timezone.utc).isoformat()
            completed_at = now_iso if status == TaskStatus.done else None

            task = Task(
                id=f"task-{int(time.time() * 1000)}",
                title=title.strip(),
                description=description.strip(),
                dueDate=due_date,
                priority=priority,
                status=status,
                position=position,
                completedAt=completed_at,
            )
            tasks.append(task)
            self._normalize_positions_locked(user_id)
            return copy.deepcopy(task)

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
        with self._lock:
            tasks = self.tasks_by_user.get(user_id, [])
            target = None
            for t in tasks:
                if t.id == task_id:
                    target = t
                    break

            if not target:
                return None

            if title is not None:
                target.title = title.strip()
            if description is not None:
                target.description = description.strip()
            if due_date is not None:
                target.dueDate = due_date
            if priority is not None:
                target.priority = priority

            if status is not None and status != target.status:
                old_status = target.status
                target.status = status
                if status == TaskStatus.done and old_status != TaskStatus.done:
                    target.completedAt = datetime.now(timezone.utc).isoformat()
                elif status != TaskStatus.done:
                    target.completedAt = None

                dest_tasks = [t for t in tasks if t.status == status and t.id != task_id]
                target.position = len(dest_tasks)
                self._normalize_positions_locked(user_id)

            return copy.deepcopy(target)

    def move_task(
        self,
        user_id: str,
        task_id: str,
        status: TaskStatus,
        target_id: Optional[str] = None,
        position: Optional[int] = None,
    ) -> Optional[List[Task]]:
        with self._lock:
            tasks = self.tasks_by_user.get(user_id, [])
            moving_task = None
            for t in tasks:
                if t.id == task_id:
                    moving_task = t
                    break

            if not moving_task:
                return None

            old_status = moving_task.status

            # Separate destination column tasks and other tasks
            dest_tasks = [t for t in tasks if t.status == status and t.id != task_id]
            dest_tasks.sort(key=lambda t: t.position)

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
                old_col_tasks = [t for t in tasks if t.status == old_status and t.id != task_id]
                old_col_tasks.sort(key=lambda t: t.position)
                for idx, t in enumerate(old_col_tasks):
                    t.position = idx

            # Rebuild user tasks with new destination list
            remaining_tasks = [t for t in tasks if t.status != status and t.id != task_id]
            self.tasks_by_user[user_id] = remaining_tasks + dest_tasks
            self._normalize_positions_locked(user_id)

            return [copy.deepcopy(t) for t in sorted(self.tasks_by_user[user_id], key=lambda x: (x.status.value, x.position))]

    def delete_task(self, user_id: str, task_id: str) -> bool:
        with self._lock:
            tasks = self.tasks_by_user.get(user_id, [])
            initial_len = len(tasks)
            self.tasks_by_user[user_id] = [t for t in tasks if t.id != task_id]
            if len(self.tasks_by_user[user_id]) < initial_len:
                self._normalize_positions_locked(user_id)
                return True
            return False

    def clear_completed(self, user_id: str) -> int:
        with self._lock:
            tasks = self.tasks_by_user.get(user_id, [])
            active_tasks = [t for t in tasks if t.status != TaskStatus.done]
            cleared_count = len(tasks) - len(active_tasks)
            self.tasks_by_user[user_id] = active_tasks
            self._normalize_positions_locked(user_id)
            return cleared_count


store = InMemoryStore()
