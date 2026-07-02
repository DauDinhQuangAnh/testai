"""Trang chu Streamlit. Chay: streamlit run app/Home.py
Sidebar dieu huong sang Upload/Dashboard duoc Streamlit tu tao tu app/pages/.
"""
import sys
from pathlib import Path

import streamlit as st

# Streamlit chi tu them thu muc chua file dang chay vao sys.path, KHONG tu them
# goc repo - can them thu cong de "from app...." hoat dong dung. Tim goc repo
# bang marker file pyproject.toml.
for _parent in Path(__file__).resolve().parents:
    if (_parent / "pyproject.toml").exists():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from app.auth.streamlit_helpers import get_current_user, logout
from app.db.session import make_session_factory

st.set_page_config(page_title="AI Subtitle Studio")
make_session_factory()  # dam bao bang DB da duoc tao

st.title("AI Subtitle Studio")
st.write(
    "Chon **Upload** o sidebar de tai video/audio len va tao job phu de, "
    "**Dashboard** de theo doi trang thai job, **Editor** de chinh sua phu de, "
    "hoac **Billing** de xem goi cuoc."
)

current_user = get_current_user()
with st.sidebar:
    if current_user:
        st.write(f"Dang nhap: {current_user.email}")
        if st.button("Dang xuat"):
            logout()
            st.rerun()
    else:
        st.caption("Chua dang nhap - vao trang Upload/Dashboard de dang nhap.")
