"""Trang dashboard: liet ke job voi progress bar theo stage, tu lam moi moi 3
giay khi dang co job chay (st.fragment run_every - can streamlit>=1.37), tai
ket qua, xoa job (ca record DB lan file tren dia - du an ca nhan nen xoa thang
khong can thung rac/soft-delete).
"""

import shutil
import sys
from pathlib import Path

import streamlit as st

for _parent in Path(__file__).resolve().parents:
    if (_parent / "pyproject.toml").exists():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from app.db.models import JobStatus
from app.jobs.repository import JobRepository
from app.ui import stage_progress, status_icon, status_label

st.set_page_config(
    page_title="Dashboard - AI Subtitle Studio", page_icon=":material/monitoring:", layout="wide"
)
st.title("Dashboard job")

FILTER_ALL = "Tất cả"
FILTER_RUNNING = "Đang xử lý"
FILTER_DONE = "Hoàn thành"
FILTER_FAILED = "Thất bại"


def _render_job(job) -> None:
    with st.expander(
        f"{job.filename} - {status_label(job)} ({job.id[:8]})",
        icon=status_icon(job),
        expanded=job.status == JobStatus.RUNNING,
    ):
        if job.status in (JobStatus.QUEUED, JobStatus.RUNNING):
            fraction, label = stage_progress(job.stage)
            st.progress(fraction, text=f"Bước hiện tại: {label}")
        if job.error_message:
            st.warning(job.error_message)
        st.caption(f"Tạo lúc: {job.created_at} | Cập nhật: {job.updated_at}")

        if job.status == JobStatus.DONE:
            output_dir = Path(job.output_dir)
            files = sorted(output_dir.glob("*.*"))
            download_columns = st.columns(3)
            for index, file in enumerate(files):
                download_columns[index % 3].download_button(
                    label=file.name,
                    data=file.read_bytes(),
                    file_name=file.name,
                    key=f"{job.id}-{file.name}",
                    icon=":material/download:",
                    use_container_width=True,
                )

        st.divider()
        confirm_delete = st.checkbox(
            "Xác nhận xóa (xóa vĩnh viễn cả video gốc lẫn kết quả trên đĩa)",
            key=f"confirm-delete-{job.id}",
        )
        if st.button(
            "Xóa job",
            key=f"delete-{job.id}",
            disabled=not confirm_delete,
            icon=":material/delete:",
        ):
            job_dir = Path(job.output_dir).parent
            shutil.rmtree(job_dir, ignore_errors=True)
            JobRepository().delete(job.id)
            st.rerun(scope="app")


@st.fragment(run_every=3.0)
def _render_dashboard() -> None:
    """Fragment tu chay lai moi 3s de cap nhat tien do ma khong can bam nut
    lam moi thu cong (chi phan nay rerun, khong rerun ca trang).
    """
    jobs = JobRepository().list_all()

    running = sum(1 for j in jobs if j.status in (JobStatus.QUEUED, JobStatus.RUNNING))
    done = sum(1 for j in jobs if j.status == JobStatus.DONE)
    failed = sum(1 for j in jobs if j.status == JobStatus.FAILED)
    col_total, col_running, col_done, col_failed = st.columns(4)
    col_total.metric("Tổng số job", len(jobs))
    col_running.metric("Đang xử lý", running)
    col_done.metric("Hoàn thành", done)
    col_failed.metric("Thất bại", failed)

    if not jobs:
        st.info("Chưa có job nào. Vào trang Upload để tạo job mới.")
        st.page_link("pages/1_Upload.py", label="Upload video/audio", icon=":material/upload:")
        return

    status_filter = st.segmented_control(
        "Lọc theo trạng thái",
        options=[FILTER_ALL, FILTER_RUNNING, FILTER_DONE, FILTER_FAILED],
        default=FILTER_ALL,
    )
    visible_jobs = {
        FILTER_ALL: jobs,
        FILTER_RUNNING: [j for j in jobs if j.status in (JobStatus.QUEUED, JobStatus.RUNNING)],
        FILTER_DONE: [j for j in jobs if j.status == JobStatus.DONE],
        FILTER_FAILED: [j for j in jobs if j.status == JobStatus.FAILED],
    }[status_filter or FILTER_ALL]

    for job in visible_jobs:
        _render_job(job)


_render_dashboard()
