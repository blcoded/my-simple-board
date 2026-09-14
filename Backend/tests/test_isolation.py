def test_user_data_isolation(client, ada_headers, new_user_headers):
    # Ada has 9 tasks initially
    ada_tasks = client.get("/api/tasks", headers=ada_headers).json()
    assert len(ada_tasks) == 9
    ada_task_id = ada_tasks[0]["id"]

    # Bob has 0 tasks initially
    bob_tasks = client.get("/api/tasks", headers=new_user_headers).json()
    assert len(bob_tasks) == 0

    # Bob attempts to access Ada's task
    get_res = client.get(f"/api/tasks/{ada_task_id}", headers=new_user_headers)
    assert get_res.status_code == 404

    # Bob attempts to patch Ada's task
    patch_res = client.patch(f"/api/tasks/{ada_task_id}", json={"title": "Hacked"}, headers=new_user_headers)
    assert patch_res.status_code == 404

    # Bob attempts to move Ada's task
    move_res = client.post(f"/api/tasks/{ada_task_id}/move", json={"status": "done"}, headers=new_user_headers)
    assert move_res.status_code == 404

    # Bob attempts to delete Ada's task
    del_res = client.delete(f"/api/tasks/{ada_task_id}", headers=new_user_headers)
    assert del_res.status_code == 404

    # Bob creates a completed task and calls clear_completed
    client.post("/api/tasks", json={"title": "Bob completed", "status": "done"}, headers=new_user_headers)
    bob_clear = client.delete("/api/tasks/completed", headers=new_user_headers)
    assert bob_clear.status_code == 204

    # Ada's done tasks must remain untouched
    ada_tasks_after = client.get("/api/tasks", headers=ada_headers).json()
    ada_done = [t for t in ada_tasks_after if t["status"] == "done"]
    assert len(ada_done) == 2
