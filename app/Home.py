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
    "Tự động tạo phụ đề và lồng tiếng cho video/audio - toàn bộ pipeline AI "
    "chạy trên máy của bạn (riêng giọng đọc dùng edge-tts, cần internet)."
)

jobs = JobRepository().list_all()
running = sum(1 for j in jobs if j.status in (JobStatus.QUEUED, JobStatus.RUNNING))
done = sum(1 for j in jobs if j.status == JobStatus.DONE)
failed = sum(1 for j in jobs if j.status == JobStatus.FAILED)

col_total, col_running, col_done, col_failed = st.columns(4)
col_total.metric("Tổng số job", len(jobs))
col_running.metric("Đang xử lý", running)
col_done.metric("Hoàn thành", done)
col_failed.metric("Thất bại", failed)

st.divider()

col_flow, col_nav = st.columns([3, 2])

with col_flow:
    st.subheader("Quy trình 3 bước")
    st.markdown(
        """
1. **Upload** - chọn video/audio, chọn ngôn ngữ + giọng lồng tiếng (hoặc chỉ
   tạo phụ đề). Hệ thống tự chạy: tách âm, khử ồn, nhận diện lời nói, dịch,
   lồng tiếng.
2. **Dashboard** - theo dõi tiến độ từng bước, tải kết quả (SRT/VTT/ASS/TXT/
   JSON + video đã lồng tiếng), xóa job cũ.
3. **Editor** - chỉnh sửa nội dung/thời gian phụ đề, dịch hoặc lồng tiếng lại
   sang ngôn ngữ/giọng khác.
"""
    )

with col_nav:
    st.subheader("Bắt đầu")
    st.page_link("pages/1_Upload.py", label="Upload video/audio", icon=":material/upload:")
    st.page_link("pages/2_Dashboard.py", label="Dashboard job", icon=":material/monitoring:")
    st.page_link("pages/3_Editor.py", label="Subtitle Editor", icon=":material/edit:")
    if running:
        st.info(f"Có {running} job đang xử lý - xem tiến độ ở Dashboard.")
