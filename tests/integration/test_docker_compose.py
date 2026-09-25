"""Integration Tests against the Containerized Application Stack (docker-compose.yaml)

Tests the live integration between:
1. PostgreSQL service ('postgres')
2. FastAPI backend + Frontend static assets ('app')
"""

import pytest
import re


class TestServiceHealth:
    """Scenario 1: Container and service health checks."""

    def test_root_health_check(self, http_client):
        """Verify the /health endpoint responds with status ok."""
        res = http_client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "ok"
        assert data.get("service") == "mini-kanban-backend"

    def test_api_health_check(self, http_client):
        """Verify the /api/health endpoint responds with status ok."""
        res = http_client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "ok"


class TestFrontendServing:
    """Scenario 2: Frontend static asset and SPA routing delivery by backend."""

    def test_root_serves_spa_html(self, http_client):
        """Verify GET / returns the compiled single-page application HTML entry."""
        res = http_client.get("/")
        assert res.status_code == 200
        content_type = res.headers.get("content-type", "")
        assert "text/html" in content_type
        assert '<div id="root"></div>' in res.text
        assert "Korda — Personal Kanban" in res.text

    def test_spa_client_side_routing_fallback(self, http_client):
        """Verify non-API URL paths return index.html to enable client-side SPA routing."""
        for path in ["/board", "/login", "/settings", "/app/tasks/view"]:
            res = http_client.get(path)
            assert res.status_code == 200
            content_type = res.headers.get("content-type", "")
            assert "text/html" in content_type
            assert '<div id="root"></div>' in res.text

    def test_static_assets_delivery(self, http_client):
        """Verify linked static assets (CSS, JS) referenced in HTML are accessible."""
        root_res = http_client.get("/")
        assert root_res.status_code == 200

        # Extract asset paths from link/script tags
        asset_matches = re.findall(r'(?:href|src)="(/assets/[^"]+)"', root_res.text)
        assert len(asset_matches) > 0, "No assets found in index.html"

        for asset_path in asset_matches:
            asset_res = http_client.get(asset_path)
            assert asset_res.status_code == 200, f"Failed to fetch asset: {asset_path}"
            assert len(asset_res.content) > 0


class TestAuthenticationWithPostgres:
    """Scenario 3: Authentication workflows backed by PostgreSQL."""

    def test_registration_and_session(self, http_client, registered_user):
        """Verify user is stored in PostgreSQL and can verify session via JWT."""
        res = http_client.get("/api/auth/session", headers=registered_user["headers"])
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == registered_user["email"]
        assert data["id"] == registered_user["id"]

    def test_duplicate_registration_rejected(self, http_client, registered_user):
        """Verify duplicate registration fails with HTTP 400 (unique constraint)."""
        res = http_client.post(
            "/api/auth/register",
            json={
                "email": registered_user["email"],
                "password": "AnotherPassword123!",
            },
        )
        assert res.status_code == 400
        assert "already exists" in res.text.lower() or "already registered" in res.text.lower()

    def test_login_flow(self, http_client, registered_user):
        """Verify user can authenticate against hashed passwords in PostgreSQL."""
        # Valid login
        res = http_client.post(
            "/api/auth/login",
            json={
                "email": registered_user["email"],
                "password": registered_user["password"],
            },
        )
        assert res.status_code == 200
        assert "token" in res.json()

        # Invalid password
        bad_res = http_client.post(
            "/api/auth/login",
            json={
                "email": registered_user["email"],
                "password": "WrongPassword!999",
            },
        )
        assert bad_res.status_code == 401

    def test_unauthenticated_request_rejected(self, http_client):
        """Verify protected endpoints reject requests lacking valid authorization."""
        res = http_client.get("/api/tasks")
        assert res.status_code in (401, 403)


class TestTaskLifecycleWithPostgres:
    """Scenario 4: Task CRUD, ordering, and movement stored in PostgreSQL."""

    def test_create_and_list_tasks(self, http_client, registered_user):
        """Verify task creation persists across columns in PostgreSQL."""
        headers = registered_user["headers"]

        # 1. Create a task in 'ideas' column
        create_res = http_client.post(
            "/api/tasks",
            headers=headers,
            json={
                "title": "Design dark mode theme",
                "description": "Evaluate high-contrast color palette",
                "priority": "high",
                "status": "ideas",
                "dueDate": "2026-10-15",
            },
        )
        assert create_res.status_code == 201
        task = create_res.json()
        assert task["title"] == "Design dark mode theme"
        assert task["priority"] == "high"
        assert task["status"] == "ideas"
        task_id = task["id"]

        # 2. Retrieve tasks list
        list_res = http_client.get("/api/tasks", headers=headers)
        assert list_res.status_code == 200
        tasks = list_res.json()
        assert any(t["id"] == task_id for t in tasks)

    def test_update_task(self, http_client, registered_user):
        """Verify updating title, description, and priority updates PostgreSQL."""
        headers = registered_user["headers"]

        # Create
        task = http_client.post(
            "/api/tasks",
            headers=headers,
            json={"title": "Original Task", "priority": "low", "status": "todo"},
        ).json()

        # Update
        patch_res = http_client.patch(
            f"/api/tasks/{task['id']}",
            headers=headers,
            json={"title": "Updated Task Title", "priority": "medium"},
        )
        assert patch_res.status_code == 200
        updated = patch_res.json()
        assert updated["title"] == "Updated Task Title"
        assert updated["priority"] == "medium"

    def test_move_task_sets_completed_at(self, http_client, registered_user):
        """Verify moving task to 'done' sets completedAt timestamp in PostgreSQL."""
        headers = registered_user["headers"]

        task = http_client.post(
            "/api/tasks",
            headers=headers,
            json={"title": "Feature QA", "priority": "high", "status": "progress"},
        ).json()
        assert task.get("completedAt") is None

        # Move to 'done'
        move_res = http_client.post(
            f"/api/tasks/{task['id']}/move",
            headers=headers,
            json={"status": "done"},
        )
        assert move_res.status_code == 200
        updated_tasks = move_res.json()
        done_task = next(t for t in updated_tasks if t["id"] == task["id"])
        assert done_task["status"] == "done"
        assert done_task["completedAt"] is not None

    def test_clear_completed_tasks(self, http_client, registered_user):
        """Verify DELETE /api/tasks/completed removes only tasks in the 'done' column."""
        headers = registered_user["headers"]

        # Create one in 'todo' and one in 'done'
        t_todo = http_client.post(
            "/api/tasks",
            headers=headers,
            json={"title": "Keep Me", "status": "todo"},
        ).json()
        t_done = http_client.post(
            "/api/tasks",
            headers=headers,
            json={"title": "Remove Me", "status": "done"},
        ).json()

        # Clear completed
        del_res = http_client.delete("/api/tasks/completed", headers=headers)
        assert del_res.status_code in (200, 204)

        # Verify
        tasks = http_client.get("/api/tasks", headers=headers).json()
        task_ids = [t["id"] for t in tasks]
        assert t_todo["id"] in task_ids
        assert t_done["id"] not in task_ids


class TestMultiTenantDataIsolation:
    """Scenario 5: User data isolation in PostgreSQL."""

    def test_users_cannot_access_each_others_tasks(
        self, http_client, registered_user, second_user
    ):
        """Verify User B cannot view, edit, or delete tasks belonging to User A."""
        user_a_headers = registered_user["headers"]
        user_b_headers = second_user["headers"]

        # User A creates a task
        task_a = http_client.post(
            "/api/tasks",
            headers=user_a_headers,
            json={"title": "Confidential User A Task", "status": "ideas"},
        ).json()

        # User B lists tasks - User A's task must not be present
        b_tasks = http_client.get("/api/tasks", headers=user_b_headers).json()
        assert not any(t["id"] == task_a["id"] for t in b_tasks)

        # User B attempts to patch User A's task -> 404
        patch_res = http_client.patch(
            f"/api/tasks/{task_a['id']}",
            headers=user_b_headers,
            json={"title": "Compromised Title"},
        )
        assert patch_res.status_code == 404

        # User B attempts to delete User A's task -> 404
        del_res = http_client.delete(
            f"/api/tasks/{task_a['id']}",
            headers=user_b_headers,
        )
        assert del_res.status_code == 404


class TestValidationAndErrorHandling:
    """Scenario 6: Input validation and HTTP status codes."""

    def test_invalid_task_returns_422(self, http_client, registered_user):
        """Verify invalid enum or empty title returns 422 Unprocessable Entity."""
        headers = registered_user["headers"]

        # Invalid priority enum
        res = http_client.post(
            "/api/tasks",
            headers=headers,
            json={"title": "Invalid Priority Task", "priority": "extreme_urgent"},
        )
        assert res.status_code == 422
        data = res.json()
        assert data.get("statusCode") == 422
