"""Hash/verify mat khau bang bcrypt, va tao/xac minh session token (JWT).

Streamlit khong co session/cookie manager rieng nhu web framework thuc thu
(xem docs/memory/dev-machine-rtx4050.md) - token nay duoc luu trong cookie
trinh duyet qua extra-streamlit-components (xem streamlit_helpers.py) de giu
dang nhap qua cac lan tai lai trang.
"""
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

SESSION_TOKEN_TTL_HOURS = 24 * 7
JWT_ALGORITHM = "HS256"


def _secret_key() -> str:
    key = os.environ.get("SESSION_SECRET_KEY")
    if not key:
        raise RuntimeError("SESSION_SECRET_KEY chua duoc set - xem .env.example")
    return key


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def create_session_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=SESSION_TOKEN_TTL_HOURS),
    }
    return jwt.encode(payload, _secret_key(), algorithm=JWT_ALGORITHM)


def verify_session_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, _secret_key(), algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
    return payload.get("user_id")
