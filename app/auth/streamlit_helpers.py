"""Helper dung trong cac trang Streamlit de bat buoc dang nhap.

Streamlit khong co session/cookie manager manh nhu web framework thuc thu, nen
dung extra-streamlit-components CookieManager de luu session token qua cac lan
tai lai trang (xem docs/memory/dev-machine-rtx4050.md va HANDOFF.md Phase 6 ve
gioi han/rui ro cua cach tiep can nay - CHUA duoc kiem thu tren trinh duyet
that).
"""
import extra_streamlit_components as stx
import streamlit as st

from app.auth.repository import UserRepository
from app.auth.security import (
    create_session_token,
    hash_password,
    verify_password,
    verify_session_token,
)
from app.db.models import User

COOKIE_NAME = "subtitle_studio_session"


def _cookie_manager() -> stx.CookieManager:
    if "_cookie_manager" not in st.session_state:
        st.session_state["_cookie_manager"] = stx.CookieManager()
    return st.session_state["_cookie_manager"]


def get_current_user() -> User | None:
    if "user_id" in st.session_state:
        return UserRepository().get_by_id(st.session_state["user_id"])

    token = _cookie_manager().get(COOKIE_NAME)
    if not token:
        return None
    user_id = verify_session_token(token)
    if not user_id:
        return None
    user = UserRepository().get_by_id(user_id)
    if user:
        st.session_state["user_id"] = user.id
    return user


def _login_user(user: User) -> None:
    st.session_state["user_id"] = user.id
    _cookie_manager().set(COOKIE_NAME, create_session_token(user.id))


def logout() -> None:
    st.session_state.pop("user_id", None)
    _cookie_manager().delete(COOKIE_NAME)


def require_login() -> User:
    user = get_current_user()
    if user is not None:
        return user

    st.title("Dang nhap")
    tab_login, tab_register = st.tabs(["Dang nhap", "Dang ky"])
    repo = UserRepository()

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Mat khau", type="password")
            if st.form_submit_button("Dang nhap"):
                existing = repo.get_by_email(email)
                if existing and verify_password(password, existing.password_hash):
                    _login_user(existing)
                    st.rerun()
                else:
                    st.error("Email hoac mat khau khong dung.")

    with tab_register:
        with st.form("register_form"):
            reg_email = st.text_input("Email", key="register_email")
            reg_password = st.text_input("Mat khau", type="password", key="register_password")
            if st.form_submit_button("Dang ky"):
                if repo.get_by_email(reg_email):
                    st.error("Email da duoc dang ky.")
                else:
                    new_user = repo.create(reg_email, hash_password(reg_password))
                    _login_user(new_user)
                    st.rerun()

    st.stop()
