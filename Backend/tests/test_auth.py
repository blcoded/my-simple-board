def test_login_success(client):
    res = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "focus"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "ada@example.com"
    assert "token" in data
    assert data["user"]["id"] == "ada@example.com"


def test_login_invalid_password(client):
    res = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "wrongpassword"})
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["message"]


def test_login_nonexistent_user(client):
    res = client.post("/api/auth/login", json={"email": "ghost@example.com", "password": "focus"})
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["message"]


def test_login_short_password(client):
    res = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "123"})
    assert res.status_code == 400
    assert "at least four characters" in res.json()["message"]


def test_register_success(client):
    res = client.post("/api/auth/register", json={"email": "carol@example.com", "password": "password123"})
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "carol@example.com"
    assert "token" in data
    assert data["user"]["id"] == "carol@example.com"


def test_register_invalid_email(client):
    res = client.post("/api/auth/register", json={"email": "not-an-email", "password": "password123"})
    assert res.status_code == 400
    assert "valid email" in res.json()["message"]


def test_register_short_password(client):
    res = client.post("/api/auth/register", json={"email": "valid@example.com", "password": "abc"})
    assert res.status_code == 400
    assert "at least four characters" in res.json()["message"]


def test_register_duplicate_email(client):
    res = client.post("/api/auth/register", json={"email": "ada@example.com", "password": "newpassword"})
    assert res.status_code == 400
    assert "already exists" in res.json()["message"]


def test_logout_authenticated(client, ada_headers):
    res = client.post("/api/auth/logout", headers=ada_headers)
    assert res.status_code == 200
    assert res.json()["message"] == "Successfully signed out."


def test_logout_unauthenticated(client):
    res = client.post("/api/auth/logout")
    assert res.status_code == 401
    assert "Authentication required" in res.json()["message"]


def test_session_unauthenticated(client):
    res = client.get("/api/auth/session")
    assert res.status_code == 200
    assert res.json() is None


def test_session_authenticated(client, ada_headers):
    res = client.get("/api/auth/session", headers=ada_headers)
    assert res.status_code == 200
    assert res.json() == {"id": "ada@example.com", "email": "ada@example.com"}


def test_invalid_jwt_token(client):
    res = client.get("/api/tasks", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert res.status_code == 401
    assert "Invalid or expired session token" in res.json()["message"]


def test_cookie_authentication(client, ada_token):
    client.cookies.set("session_token", ada_token)
    res = client.get("/api/tasks")
    assert res.status_code == 200
    assert len(res.json()) == 9


def test_auth_routes_without_api_prefix(client):
    res = client.post("/auth/login", json={"email": "ada@example.com", "password": "focus"})
    assert res.status_code == 200
    assert "token" in res.json()
