"""Dang ky/dang nhap. Admin la tai khoan CHUNG tu env (check truoc bang
users) - dang nhap bang cap do se nhan token role=admin.
"""

from fastapi import APIRouter, Depends, HTTPException

from backend.db import user_repo
from backend.schemas import LoginIn, RegisterIn, TokenOut, UserOut
from backend.security import (
    ADMIN_ROLE,
    USER_ROLE,
    AuthUser,
    admin_credentials,
    create_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
def register(body: RegisterIn) -> TokenOut:
    repo = user_repo()
    if repo.get_by_email(body.email):
        raise HTTPException(status_code=409, detail="Email đã được đăng ký")
    user = repo.create(body.email, hash_password(body.password))
    return TokenOut(
        token=create_token(user.id, USER_ROLE),
        role=USER_ROLE,
        user=UserOut(id=user.id, email=user.email, created_at=user.created_at),
    )


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn) -> TokenOut:
    admin_email, admin_password = admin_credentials()
    if body.email == admin_email and body.password == admin_password:
        return TokenOut(
            token=create_token("admin", ADMIN_ROLE),
            role=ADMIN_ROLE,
            user=UserOut(id="admin", email=admin_email),
        )

    user = user_repo().get_by_email(body.email)
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")
    return TokenOut(
        token=create_token(user.id, USER_ROLE),
        role=USER_ROLE,
        user=UserOut(id=user.id, email=user.email, created_at=user.created_at),
    )


@router.get("/me", response_model=UserOut)
def me(user: AuthUser = Depends(get_current_user)) -> UserOut:
    return UserOut(id=user.id, email=user.email)
