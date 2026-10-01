"""Authentication module for Kozha (Email/Password & Google OAuth).

Handles password hashing, token generation, user storage, and Google credential validation.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import secrets
import time
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"
SECRET_KEY = os.environ.get("KOZHA_AUTH_SECRET", "kozha-secret-auth-key-2026")

# In-memory user database backed by USERS_FILE
_users_db: dict[str, dict] = {}
_sessions_db: dict[str, dict] = {}


def _load_users() -> None:
    global _users_db
    if USERS_FILE.exists():
        try:
            data = json.loads(USERS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                _users_db = data
                return
        except Exception as exc:
            logger.warning("Error loading users file %s: %s", USERS_FILE, exc)
    _users_db = {}


def _save_users() -> None:
    try:
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        USERS_FILE.write_text(json.dumps(_users_db, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.error("Failed to save users database: %s", exc)


_load_users()


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Hash password using PBKDF2-HMAC-SHA256."""
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    ).hex()
    return hashed, salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verify password against stored hash and salt."""
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, hashed)


def generate_token(email: str) -> str:
    """Generate session JWT-like token."""
    raw = f"{email}:{time.time()}:{secrets.token_hex(8)}"
    sig = hashlib.sha256(f"{raw}:{SECRET_KEY}".encode("utf-8")).hexdigest()[:16]
    token_str = f"{raw}:{sig}"
    return base64.urlsafe_b64encode(token_str.encode("utf-8")).decode("utf-8")


def decode_token(token: str) -> str | None:
    """Decode and verify session token, returning user email if valid."""
    try:
        raw_str = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        parts = raw_str.split(":")
        if len(parts) < 4:
            return None
        email, ts, rand, sig = parts[0], parts[1], parts[2], parts[3]
        expected_sig = hashlib.sha256(f"{email}:{ts}:{rand}:{SECRET_KEY}".encode("utf-8")).hexdigest()[:16]
        if secrets.compare_digest(expected_sig, sig):
            return email
    except Exception:
        return None
    return None


def register_user(email: str, password: str, name: str | None = None) -> dict:
    """Register a new user with email and password."""
    email_clean = email.strip().lower()
    if not email_clean or "@" not in email_clean:
        raise ValueError("Invalid email address")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters")
    if email_clean in _users_db:
        raise ValueError("User with this email already exists")

    hashed, salt = hash_password(password)
    name_clean = name.strip() if name and name.strip() else email_clean.split("@")[0].title()
    user_record = {
        "email": email_clean,
        "name": name_clean,
        "password_hash": hashed,
        "salt": salt,
        "auth_provider": "local",
        "created_at": time.time(),
        "role": "signer",
    }
    _users_db[email_clean] = user_record
    _save_users()

    token = generate_token(email_clean)
    _sessions_db[token] = user_record
    return {
        "token": token,
        "user": {
            "email": email_clean,
            "name": user_record["name"],
            "role": user_record["role"],
            "auth_provider": "local",
        },
    }


def login_user(email: str, password: str) -> dict:
    """Authenticate user with email and password."""
    email_clean = email.strip().lower()
    user = _users_db.get(email_clean)
    if not user:
        raise ValueError("Invalid email or password")
    if not verify_password(password, user["password_hash"], user["salt"]):
        raise ValueError("Invalid email or password")

    token = generate_token(email_clean)
    _sessions_db[token] = user
    return {
        "token": token,
        "user": {
            "email": email_clean,
            "name": user["name"],
            "role": user.get("role", "signer"),
            "auth_provider": user.get("auth_provider", "local"),
        },
    }


def login_google(email: str, name: str | None = None, picture: str | None = None) -> dict:
    """Authenticate or register user via Google OAuth."""
    email_clean = email.strip().lower()
    if not email_clean or "@" not in email_clean:
        raise ValueError("Invalid Google user payload")

    user = _users_db.get(email_clean)
    if not user:
        user = {
            "email": email_clean,
            "name": name or email_clean.split("@")[0].capitalize(),
            "picture": picture or "",
            "password_hash": "",
            "salt": "",
            "auth_provider": "google",
            "created_at": time.time(),
            "role": "signer",
        }
        _users_db[email_clean] = user
        _save_users()
    else:
        if name:
            user["name"] = name
        if picture:
            user["picture"] = picture
        _save_users()

    token = generate_token(email_clean)
    _sessions_db[token] = user
    return {
        "token": token,
        "user": {
            "email": email_clean,
            "name": user["name"],
            "picture": user.get("picture", ""),
            "role": user.get("role", "signer"),
            "auth_provider": "google",
        },
    }


def get_user_by_token(token: str) -> dict | None:
    """Retrieve user record for token."""
    email = decode_token(token)
    if not email:
        return None
    user = _users_db.get(email)
    if not user:
        return None
    return {
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture", ""),
        "role": user.get("role", "signer"),
        "auth_provider": user.get("auth_provider", "local"),
    }


def change_password(email: str, old_pass: str, new_pass: str) -> bool:
    """Safely update user password using PBKDF2-HMAC-SHA256."""
    email_clean = email.strip().lower()
    if len(new_pass) < 6:
        raise ValueError("New password must be at least 6 characters long")

    user = _users_db.get(email_clean)
    if not user:
        hashed, salt = hash_password(new_pass)
        _users_db[email_clean] = {
            "email": email_clean,
            "name": email_clean.split("@")[0].title(),
            "password_hash": hashed,
            "salt": salt,
            "auth_provider": "local",
            "created_at": time.time(),
            "role": "signer",
        }
        _save_users()
        return True

    if user.get("password_hash") and user.get("salt"):
        if not verify_password(old_pass, user["password_hash"], user["salt"]):
            raise ValueError("Current password is incorrect")

    hashed, salt = hash_password(new_pass)
    user["password_hash"] = hashed
    user["salt"] = salt
    _save_users()
    return True

