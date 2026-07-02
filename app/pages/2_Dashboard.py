"""Trang dashboard: liet ke job, trang thai/tien do, tai file ket qua khi xong."""
import sys
from pathlib import Path

import streamlit as st

for _parent in Path(__file__).resolve().parents:
    if (_parent / "pyproject.toml").exists():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from app.auth.streamlit_helpers import require_login
from app.db.models import JobStatus
from app.jobs.repository import JobRepository

st.set_page_config(page_title="Dashboard - AI Subtitle Studio")
user = require_login()
st.title("Dashboard job")

if st.button("Lam moi"):
    st.rerun()

repo = JobRepository()
jobs = repo.list_by_user(user.id)

if not jobs:
    st.info("Chua co job nao. Vao trang Upload de tao job moi.")

for job in jobs:
    with st.expander(f"{job.filename} - {job.status.value} ({job.id[:8]})"):
        st.write(f"Trang thai: **{job.status.value}**")
        if job.stage:
            st.write(f"Buoc hien tai: {job.stage}")
        if job.error_message:
            st.error(job.error_message)
        st.caption(f"Tao luc: {job.created_at} | Cap nhat: {job.updated_at}")

        if job.status == JobStatus.DONE:
            output_dir = Path(job.output_dir)
            for file in sorted(output_dir.glob("*.*")):
                st.download_button(
                    label=f"Tai {file.name}",
                    data=file.read_bytes(),
                    file_name=file.name,
                    key=f"{job.id}-{file.name}",
                )
