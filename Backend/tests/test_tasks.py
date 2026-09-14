def test_list_tasks_seeded(client, ada_headers):
    res = client.get("/api/tasks", headers=ada_headers)
    assert res.status_code == 200
    tasks = res.json()
    assert len(tasks) == 9

    statuses = {t["status"] for t in tasks}
    assert statuses == {"ideas", "todo", "progress", "done"}


def test_list_tasks_empty_user(client, new_user_headers):
    res = client.get("/api/tasks", headers=new_user_headers)
    assert res.status_code == 200
    assert res.json() == []


def test_create_task_default_values(client, new_user_headers):
    payload = {
        "title": "Minimal task",
        "status": "ideas",
    }
    res = client.post("/api/tasks", json=payload, headers=new_user_headers)
    assert res.status_code == 201
    created = res.json()
    assert created["title"] == "Minimal task"
    assert created["description"] == ""
    assert created["dueDate"] == ""
    assert created["priority"] == "medium"
    assert created["status"] == "ideas"
    assert created["position"] == 0
    assert created["completedAt"] is None


def test_create_task_in_done_sets_completed_at(client, new_user_headers):
    payload = {
        "title": "Already completed task",
        "status": "done",
    }
    res = client.post("/api/tasks", json=payload, headers=new_user_headers)
    assert res.status_code == 201
    created = res.json()
    assert created["status"] == "done"
    assert created["completedAt"] is not None


def test_create_task_empty_title(client, ada_headers):
    res = client.post("/api/tasks", json={"title": "   ", "status": "ideas"}, headers=ada_headers)
    assert res.status_code == 400
    assert "A task needs a title." in res.json()["message"]


def test_create_task_unauthenticated(client):
    res = client.post("/api/tasks", json={"title": "Test", "status": "ideas"})
    assert res.status_code == 401


def test_get_single_task_success(client, ada_headers):
    res = client.get("/api/tasks/task-onboarding", headers=ada_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "task-onboarding"
    assert data["title"] == "Sketch onboarding flow"


def test_get_single_task_not_found(client, ada_headers):
    res = client.get("/api/tasks/nonexistent-id", headers=ada_headers)
    assert res.status_code == 404
    assert "That task is no longer available." in res.json()["message"]


def test_update_task_fields(client, ada_headers):
    update_payload = {
        "title": "Updated sketch flow",
        "description": "Added user testing step.",
        "dueDate": "2026-04-01",
        "priority": "low",
    }
    res = client.patch("/api/tasks/task-onboarding", json=update_payload, headers=ada_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Updated sketch flow"
    assert data["description"] == "Added user testing step."
    assert data["dueDate"] == "2026-04-01"
    assert data["priority"] == "low"


def test_update_task_status_to_done_and_back(client, ada_headers):
    # Transition to done
    to_done = client.patch("/api/tasks/task-onboarding", json={"status": "done"}, headers=ada_headers)
    assert to_done.status_code == 200
    assert to_done.json()["status"] == "done"
    assert to_done.json()["completedAt"] is not None

    # Transition back to progress
    back_to_progress = client.patch("/api/tasks/task-onboarding", json={"status": "progress"}, headers=ada_headers)
    assert back_to_progress.status_code == 200
    assert back_to_progress.json()["status"] == "progress"
    assert back_to_progress.json()["completedAt"] is None


def test_update_task_empty_title_fails(client, ada_headers):
    res = client.patch("/api/tasks/task-onboarding", json={"title": " "}, headers=ada_headers)
    assert res.status_code == 400
    assert "A task needs a title." in res.json()["message"]


def test_update_task_not_found(client, ada_headers):
    res = client.patch("/api/tasks/ghost-id", json={"title": "Ghost"}, headers=ada_headers)
    assert res.status_code == 404


def test_delete_task_success(client, ada_headers):
    res = client.delete("/api/tasks/task-onboarding", headers=ada_headers)
    assert res.status_code == 204

    # Verify task is gone
    check = client.get("/api/tasks/task-onboarding", headers=ada_headers)
    assert check.status_code == 404


def test_delete_task_not_found(client, ada_headers):
    res = client.delete("/api/tasks/nonexistent-id", headers=ada_headers)
    assert res.status_code == 404


def test_clear_completed(client, ada_headers):
    res = client.delete("/api/tasks/completed", headers=ada_headers)
    assert res.status_code == 204

    # Verify done tasks are cleared while other columns remain
    list_res = client.get("/api/tasks", headers=ada_headers)
    assert list_res.status_code == 200
    remaining_tasks = list_res.json()
    assert len(remaining_tasks) == 7
    assert all(t["status"] != "done" for t in remaining_tasks)


def test_tasks_routes_without_api_prefix(client, ada_headers):
    res = client.get("/tasks", headers=ada_headers)
    assert res.status_code == 200
    assert len(res.json()) == 9
