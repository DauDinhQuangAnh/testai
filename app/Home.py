"""Trang chu Streamlit. Chay: streamlit run app/Home.py
Sidebar dieu huong sang Upload/Dashboard/Editor duoc Streamlit tu tao tu
app/pages/.
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

from app.db.models import JobStatus
from app.db.session import make_session_factory
from app.jobs.repository import JobRepository

st.set_page_config(page_title="AI Subtitle Studio", page_icon=":material/subtitles:", layout="wide")
make_session_factory()  # dam bao bang DB da duoc tao

st.title("AI Subtitle Studio")
st.caption(
    "Tu dong tao phu de va long tieng cho video/audio - toan bo pipeline AI "
    "chay tren may cua ban (rieng giong doc dung edge-tts, can internet)."
)

jobs = JobRepository().list_all()
running = sum(1 for j in jobs if j.status in (JobStatus.QUEUED, JobStatus.RUNNING))
done = sum(1 for j in jobs if j.status == JobStatus.DONE)
failed = sum(1 for j in jobs if j.status == JobStatus.FAILED)

col_total, col_running, col_done, col_failed = st.columns(4)
col_total.metric("Tong so job", len(jobs))
col_running.metric("Dang xu ly", running)
col_done.metric("Hoan thanh", done)
col_failed.metric("That bai", failed)

st.divider()

col_flow, col_nav = st.columns([3, 2])

with col_flow:
    st.subheader("Quy trinh 3 buoc")
    st.markdown(
        """
1. **Upload** - chon video/audio, chon ngon ngu + giong long tieng (hoac chi
   tao phu de). He thong tu chay: tach am, khu on, nhan dien loi noi, dich,
   long tieng.
2. **Dashboard** - theo doi tien do tung buoc, tai ket qua (SRT/VTT/ASS/TXT/
   JSON + video da long tieng), xoa job cu.
3. **Editor** - chinh sua noi dung/thoi gian phu de, dich hoac long tieng lai
   sang ngon ngu/giong khac.
"""
    )

with col_nav:
    st.subheader("Bat dau")
    st.page_link("pages/1_Upload.py", label="Upload video/audio", icon=":material/upload:")
    st.page_link("pages/2_Dashboard.py", label="Dashboard job", icon=":material/monitoring:")
    st.page_link("pages/3_Editor.py", label="Subtitle Editor", icon=":material/edit:")
    if running:
        st.info(f"Co {running} job dang xu ly - xem tien do o Dashboard.")
