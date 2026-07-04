"""Auth cho backend FastAPI: bcrypt (mat khau user), JWT bearer token, va tai
khoan admin CHUNG lay tu env `ADMIN_EMAIL`/`ADMIN_PASSWORD` (khong nam trong
bang users - ai biet cap tai khoan nay deu la admin, theo yeu cau nguoi dung
2026-07-03, xem HANDOFF.md).

Token cung duoc chap nhan qua query param `?token=` (chi o cac endpoint file)
vi the `<video>`/`<a download>` khong gui duoc header Authorization.
"""

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.db import user_repo

TOKEN_TTL_HOURS = 24 * 7
JWT_ALGORITHM = "HS256"

ADMIN_ROLE = "admin"
USER_ROLE = "user"


def _secret_key() -> str:
    # Fallback co dinh cho dev/tool ca nhan - doi qua .env khi expose ra ngoai.
    return os.environ.get("SESSION_SECRET_KEY", "dev-secret-doi-khi-deploy")


def admin_credentials() -> tuple[str, str]:
    return (
        os.environ.get("ADMIN_EMAIL", "admin@local"),
        os.environ.get("ADMIN_PASSWORD", "admin123"),
    )


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), password_hash.encode("utf-8"))


def create_token(subject: str, role: str) -> str:
    payload = {
        "sub": subject,
        "role": role,
        "exp": datetime.now(UTC) + timedelta(hours=TOKEN_TTL_HOURS),
    }
    return jwt.encode(payload, _secret_key(), algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, _secret_key(), algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


@dataclass
class AuthUser:
    id: str
    email: str
    role: str

    @property
    def is_admin(self) -> bool:
        return self.role == ADMIN_ROLE


_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    token: str | None = Query(default=None),
) -> AuthUser:
    raw = credentials.credentials if credentials else token
    if not raw:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
    payload = decode_token(raw)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn")

    if payload.get("role") == ADMIN_ROLE:
        admin_email, _ = admin_credentials()
        return AuthUser(id="admin", email=admin_email, role=ADMIN_ROLE)

    user = user_repo().get_by_id(payload.get("sub", ""))
    if user is None:
        raise HTTPException(status_code=401, detail="Tài khoản không còn tồn tại")
    return AuthUser(id=user.id, email=user.email, role=USER_ROLE)


def require_admin(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Chỉ admin được phép")
    return user
