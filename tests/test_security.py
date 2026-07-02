"""Test hash/verify mat khau va session token - khong can DB/AI deps."""
import os

os.environ.setdefault("SESSION_SECRET_KEY", "test-secret-key-for-pytest-only")

from app.auth.security import (  # noqa: E402
    create_session_token,
    hash_password,
    verify_password,
    verify_session_token,
)


def test_hash_and_verify_password_roundtrip():
    password_hash = hash_password("hunter2")

    assert verify_password("hunter2", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_session_token_roundtrip():
    token = create_session_token("user-123")

    assert verify_session_token(token) == "user-123"


def test_invalid_session_token_returns_none():
    assert verify_session_token("not-a-valid-token") is None
