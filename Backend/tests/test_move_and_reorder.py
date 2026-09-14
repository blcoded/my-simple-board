def test_move_cross_column_before_target(client, ada_headers):
    # Move task-drag-physics (from ideas) to todo before task-auth
    res = client.post(
        "/api/tasks/task-drag-physics/move",
        json={"status": "todo", "targetId": "task-auth"},
        headers=ada_headers,
    )
    assert res.status_code == 200
    tasks = res.json()

    todo_tasks = [t for t in tasks if t["status"] == "todo"]
    assert len(todo_tasks) == 4
    assert todo_tasks[0]["id"] == "task-drag-physics"
    assert todo_tasks[0]["position"] == 0
    assert todo_tasks[1]["id"] == "task-auth"
    assert todo_tasks[1]["position"] == 1


def test_move_cross_column_to_bottom(client, ada_headers):
    # Move task-onboarding to todo without targetId -> appends to bottom
    res = client.post(
        "/api/tasks/task-onboarding/move",
        json={"status": "todo"},
        headers=ada_headers,
    )
    assert res.status_code == 200
    tasks = res.json()

    todo_tasks = [t for t in tasks if t["status"] == "todo"]
    assert len(todo_tasks) == 4
    last_todo = todo_tasks[-1]
    assert last_todo["id"] == "task-onboarding"
    assert last_todo["position"] == 3


def test_move_within_same_column(client, ada_headers):
    # In todo column, tasks are [task-auth (0), task-dnd (1), task-empty-states (2)]
    # Move task-empty-states before task-auth
    res = client.post(
        "/api/tasks/task-empty-states/move",
        json={"status": "todo", "targetId": "task-auth"},
        headers=ada_headers,
    )
    assert res.status_code == 200
    tasks = res.json()

    todo_tasks = [t for t in tasks if t["status"] == "todo"]
    assert todo_tasks[0]["id"] == "task-empty-states"
    assert todo_tasks[0]["position"] == 0
    assert todo_tasks[1]["id"] == "task-auth"
    assert todo_tasks[1]["position"] == 1
    assert todo_tasks[2]["id"] == "task-dnd"
    assert todo_tasks[2]["position"] == 2


def test_move_to_done_sets_completed_at(client, ada_headers):
    res = client.post(
        "/api/tasks/task-card/move",
        json={"status": "done"},
        headers=ada_headers,
    )
    assert res.status_code == 200
    tasks = res.json()

    card_task = next(t for t in tasks if t["id"] == "task-card")
    assert card_task["status"] == "done"
    assert card_task["completedAt"] is not None


def test_move_from_done_clears_completed_at(client, ada_headers):
    # task-api is initially in done
    res = client.post(
        "/api/tasks/task-api/move",
        json={"status": "ideas"},
        headers=ada_headers,
    )
    assert res.status_code == 200
    tasks = res.json()

    api_task = next(t for t in tasks if t["id"] == "task-api")
    assert api_task["status"] == "ideas"
    assert api_task["completedAt"] is None


def test_move_nonexistent_task(client, ada_headers):
    res = client.post(
        "/api/tasks/nonexistent-task/move",
        json={"status": "todo"},
        headers=ada_headers,
    )
    assert res.status_code == 404
    assert "That task is no longer available." in res.json()["message"]


def test_position_contiguity_after_middle_deletion(client, ada_headers):
    # In ideas: [task-onboarding (0), task-tokens (1), task-drag-physics (2)]
    # Delete task-tokens
    del_res = client.delete("/api/tasks/task-tokens", headers=ada_headers)
    assert del_res.status_code == 204

    res = client.get("/api/tasks", headers=ada_headers)
    ideas = [t for t in res.json() if t["status"] == "ideas"]
    assert len(ideas) == 2
    assert ideas[0]["id"] == "task-onboarding"
    assert ideas[0]["position"] == 0
    assert ideas[1]["id"] == "task-drag-physics"
    assert ideas[1]["position"] == 1
