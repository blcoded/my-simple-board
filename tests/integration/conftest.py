import os
import time
import uuid
import pytest
import httpx

APP_URL = os.getenv("APP_URL", "http://localhost:8000").rstrip("/")


@pytest.fixture(scope="session")
def base_url() -> str:
    """Target URL of the running containerized application."""
    return APP_URL


@pytest.fixture(scope="session")
def wait_for_app(base_url):
    """Wait for the containerized application to become healthy before running tests."""
    max_wait = int(os.getenv("APP_WAIT_TIMEOUT", "30"))
    start_time = time.time()
    last_error = None

    print(f"\nWaiting for application at {base_url}/health (up to {max_wait}s)...")
    while time.time() - start_time < max_wait:
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{base_url}/health")
                if res.status_code == 200:
                    print("Application is healthy and ready for integration tests.")
                    return True
        except Exception as e:
            last_error = e
        time.sleep(1)

    pytest.fail(
        f"Application at {base_url} failed to respond within {max_wait}s. "
        f"Ensure 'docker compose up' is running. Last error: {last_error}"
    )


@pytest.fixture
def http_client(base_url, wait_for_app):
    """HTTP client configured for the target application."""
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        yield client


@pytest.fixture
def registered_user(http_client):
    """Creates a unique user for integration testing and yields auth token and headers."""
    unique_id = uuid.uuid4().hex[:8]
    email = f"integ_{unique_id}@example.com"
    password = f"SecurePass_{unique_id}!1"

    res = http_client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    assert res.status_code == 201, f"Failed to register test user: {res.text}"
    data = res.json()
    token = data["token"]

    user_info = {
        "id": data.get("id"),
        "email": email,
        "password": password,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }
    return user_info


@pytest.fixture
def second_user(http_client):
    """Creates a second distinct user for multi-tenant data isolation testing."""
    unique_id = uuid.uuid4().hex[:8]
    email = f"integ_user2_{unique_id}@example.com"
    password = f"SecurePass2_{unique_id}!2"

    res = http_client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    assert res.status_code == 201, f"Failed to register second test user: {res.text}"
    data = res.json()
    token = data["token"]

    return {
        "id": data.get("id"),
        "email": email,
        "password": password,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }
