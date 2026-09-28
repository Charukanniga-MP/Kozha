"""Unit tests for Kozha user authentication API endpoints."""
from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "server") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "server"))

from server import app  # noqa: E402
import auth  # noqa: E402


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    test_users_file = tmp_path / "test_users.json"
    monkeypatch.setattr(auth, "USERS_FILE", test_users_file)
    auth._users_db = {}
    auth._sessions_db = {}
    return TestClient(app)


def test_signup_and_login_flow(client: TestClient) -> None:
    # 1. Register new user
    signup_res = client.post(
        "/api/auth/signup",
        json={"email": "signer@example.com", "password": "securepassword123", "name": "Sarah Signer"},
    )
    assert signup_res.status_code == 200
    data = signup_res.json()
    assert "token" in data
    assert data["user"]["email"] == "signer@example.com"
    token = data["token"]

    # 2. Check /api/auth/me profile
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["user"]["name"] == "Sarah Signer"

    # 3. Login with credentials
    login_res = client.post(
        "/api/auth/login",
        json={"email": "signer@example.com", "password": "securepassword123"},
    )
    assert login_res.status_code == 200
    assert "token" in login_res.json()


def test_login_invalid_password(client: TestClient) -> None:
    client.post(
        "/api/auth/signup",
        json={"email": "test@example.com", "password": "password123"},
    )
    bad_res = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert bad_res.status_code == 401


def test_google_login_flow(client: TestClient) -> None:
    res = client.post(
        "/api/auth/google",
        json={"email": "googleuser@example.com", "name": "Google User", "picture": "https://example.com/pic.jpg"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["auth_provider"] == "google"
    assert "token" in data
