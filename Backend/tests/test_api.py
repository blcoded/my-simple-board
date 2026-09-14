import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.store import store

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_store():
    # Re-seed the store before tests
    store.__init__()


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "mini-kanban-backend"}

    res_api = client.get("/api/health")
    assert res_api.status_code == 200
    assert res_api.json() == {"status": "ok", "service": "mini-kanban-backend"}


def test_login_seeded_user_success():
    res = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "focus"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "ada@example.com"
    assert "token" in data
    assert data["user"]["email"] == "ada@example.com"


def test_login_failure():
    res = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "wrongpassword"})
    assert res.status_code == 401
    data = res.json()
    assert "Invalid email or password" in data["message"]


def test_register_new_user():
    res = client.post("/api/auth/register", json={"email": "newuser@example.com", "password": "secret123"})
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "newuser@example.com"
    assert "token" in data

    token = data["token"]
    # New user board should initially be empty
    tasks_res = client.get("/api/tasks", headers={"Authorization": f"Bearer {token}"})
    assert tasks_res.status_code == 200
    assert tasks_res.json() == []


def test_get_session():
    # Unauthenticated session returns null
    unauth = client.get("/api/auth/session")
    assert unauth.status_code == 200
    assert unauth.json() is None

    # Authenticated session
    login_res = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "focus"})
    token = login_res.json()["token"]

    auth_res = client.get("/api/auth/session", headers={"Authorization": f"Bearer {token}"})
    assert auth_res.status_code == 200
    assert auth_res.json() == {"id": "ada@example.com", "email": "ada@example.com"}


def test_tasks_require_auth():
    res = client.get("/api/tasks")
    assert res.status_code == 401
    assert "Authentication required" in res.json()["message"]


def test_seeded_tasks_loaded():
    login_res = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "focus"})
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/tasks", headers=headers)
    assert res.status_code == 200
    tasks = res.json()
    assert len(tasks) == 9

    task_ids = [t["id"] for t in tasks]
    assert "task-onboarding" in task_ids
    assert "task-auth" in task_ids
    assert "task-card" in task_ids
    assert "task-api" in task_ids


def test_task_create_and_read():
    login_res = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "focus"})
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    new_task_payload = {
        "title": "Test backend implementation",
        "description": "Ensure all endpoints match openapi spec.",
        "dueDate": "2026-03-25",
        "priority": "high",
        "status": "todo",
    }
    create_res = client.post("/api/tasks", json=new_task_payload, headers=headers)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["title"] == "Test backend implementation"
    assert created["status"] == "todo"
    assert created["priority"] == "high"

    # Get single task
    get_res = client.get(f"/api/tasks/{created['id']}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Test backend implementation"


def test_task_update_and_completed_at():
    login_res = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "focus"})
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update task to done
    patch_res = client.patch(
        "/api/tasks/task-onboarding",
        json={"status": "done", "priority": "low"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["status"] == "done"
    assert updated["priority"] == "low"
    assert updated["completedAt"] is not None

    # Update task out of done clears completedAt
    patch_out = client.patch(
        "/api/tasks/task-onboarding",
        json={"status": "ideas"},
        headers=headers,
    )
    assert patch_out.status_code == 200
    assert patch_out.json()["status"] == "ideas"
    assert patch_out.json()["completedAt"] is None


def test_task_move():
    login_res = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "focus"})
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Move task-drag-physics to todo before task-auth
    move_res = client.post(
        "/api/tasks/task-drag-physics/move",
        json={"status": "todo", "targetId": "task-auth"},
        headers=headers,
    )
    assert move_res.status_code == 200
    tasks = move_res.json()
    todo_tasks = [t for t in tasks if t["status"] == "todo"]
    assert todo_tasks[0]["id"] == "task-drag-physics"
    assert todo_tasks[0]["position"] == 0
    assert todo_tasks[1]["id"] == "task-auth"
    assert todo_tasks[1]["position"] == 1


def test_delete_task():
    login_res = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "focus"})
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    del_res = client.delete("/api/tasks/task-onboarding", headers=headers)
    assert del_res.status_code == 204

    get_res = client.get("/api/tasks/task-onboarding", headers=headers)
    assert get_res.status_code == 404


def test_clear_completed():
    login_res = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "focus"})
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    clear_res = client.delete("/api/tasks/completed", headers=headers)
    assert clear_res.status_code == 204

    tasks_res = client.get("/api/tasks", headers=headers)
    assert tasks_res.status_code == 200
    done_tasks = [t for t in tasks_res.json() if t["status"] == "done"]
    assert len(done_tasks) == 0
