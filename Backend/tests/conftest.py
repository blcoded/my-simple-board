import os
import pytest
from fastapi.testclient import TestClient

# Ensure test suite runs on an isolated in-memory SQLite database
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from backend.main import app
from backend.store import store


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_store():
    # Reset and re-seed the database before each test
    store.reset_db()


@pytest.fixture
def ada_token(client):
    res = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "focus"})
    assert res.status_code == 200
    return res.json()["token"]


@pytest.fixture
def ada_headers(ada_token):
    return {"Authorization": f"Bearer {ada_token}"}


@pytest.fixture
def new_user_headers(client):
    res = client.post("/api/auth/register", json={"email": "bob@example.com", "password": "password123"})
    assert res.status_code == 201
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}"}
