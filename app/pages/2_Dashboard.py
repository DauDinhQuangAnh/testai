"""Trang dashboard: liet ke job voi progress bar theo stage, tu lam moi moi 3
giay khi dang co job chay (st.fragment run_every - can streamlit>=1.37), tai
ket qua, xoa job (ca record DB lan file tren dia - du an ca nhan nen xoa thang
khong can thung rac/soft-delete).
"""

import json
import shutil
import sys
import uuid
from pathlib import Path

import streamlit as st

for _parent in Path(__file__).resolve().parents:
    if (_parent / "pyproject.toml").exists():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from app.config import AppConfig
from app.db.models import JobStatus
from app.jobs.repository import JobRepository
from app.jobs.tasks import process_video_job
from app.ui import render_stage_progress, status_icon, status_label

st.set_page_config(
    page_title="Dashboard - AI Subtitle Studio", page_icon=":material/monitoring:", layout="wide"
)
st.title("Dashboard job")

FILTER_ALL = "Tất cả"
FILTER_RUNNING = "Đang xử lý"
FILTER_DONE = "Hoàn thành"
FILTER_FAILED = "Thất bại"

_INTERNAL_SUFFIXES = (".source_language.txt",)


def _render_results(job) -> None:
    """Hien ket qua job DONE de xem/nghe/tai truc tiep tai Dashboard, thay vi
    liet ke phang toan bo file trong output_dir bang ten day du kho doc (moi
    file 1 nut tai giong het nhau). Quy uoc dat ten (xem
    subtitle_pipeline/export/formats.py, application/dub.py):
    `{stem}.{fmt}` = phu de goc, `{stem}.{lang}.{fmt}` = phu de da dich,
    `{stem}.{lang}.dubbed.mp4` = video da long tieng.
    """
    output_dir = Path(job.output_dir)
    stem = Path(job.input_path).stem
    files = [f for f in sorted(output_dir.glob("*.*")) if not f.name.endswith(_INTERNAL_SUFFIXES)]
    if not files:
        st.caption("Chưa có file kết quả.")
        return

    videos = [f for f in files if f.name.endswith(".dubbed.mp4")]
    subtitle_files = [f for f in files if f not in videos]

    for video in videos:
        lang = video.name.removeprefix(f"{stem}.").removesuffix(".dubbed.mp4")
        st.markdown(f"**🎬 Video đã lồng tiếng ({lang})**")
        st.video(str(video))
        st.download_button(
            f"Tải video ({lang})",
            data=video.read_bytes(),
            file_name=video.name,
            key=f"{job.id}-{video.name}",
            icon=":material/download:",
        )

    groups: dict[str, list[Path]] = {}
    for f in subtitle_files:
        rest = f.name.removeprefix(f"{stem}.")
        lang = rest.split(".")[0] if "." in rest else "Gốc"
        groups.setdefault(lang, []).append(f)

    for lang, group_files in groups.items():
        label = "Phụ đề gốc" if lang == "Gốc" else f"Phụ đề đã dịch ({lang})"
        st.markdown(f"**📝 {label}**")
        with st.expander("Xem trước nội dung (.txt)", expanded=False):
            txt_file = next((f for f in group_files if f.suffix == ".txt"), None)
            if txt_file:
                st.text(txt_file.read_text(encoding="utf-8"))
        cols = st.columns(len(group_files))
        for col, f in zip(cols, sorted(group_files, key=lambda x: x.suffix), strict=False):
            col.download_button(
                f.suffix.removeprefix(".").upper(),
                data=f.read_bytes(),
                file_name=f.name,
                key=f"{job.id}-{f.name}",
                icon=":material/download:",
                use_container_width=True,
            )


def _render_rerun_button(job) -> None:
    """Tao job MOI voi dung cau hinh cua job nay (doc `job_config.json` do
    wizard Upload luu luc tao job). Job tu URL thi worker tu tai lai; job tu
    file upload thi copy file goc sang thu muc job moi (khong tham chieu
    chung file - xoa job cu se khong lam hong job moi).
    """
    config_path = Path(job.output_dir).parent / "job_config.json"
    if not config_path.exists():
        return
    if not st.button("Tạo lại với cấu hình này", key=f"rerun-{job.id}", icon=":material/replay:"):
        return

    options = json.loads(config_path.read_text(encoding="utf-8"))
    new_id = str(uuid.uuid4())
    new_dir = AppConfig.from_env().storage_dir / new_id
    new_dir.mkdir(parents=True, exist_ok=True)

    if (options.get("source") or {}).get("url"):
        filename = options["source"]["url"]
        input_path = new_dir / "download_pending"
    else:
        source_file = Path(job.input_path)
        filename = source_file.name
        input_path = new_dir / filename
        shutil.copy2(source_file, input_path)

    (new_dir / "job_config.json").write_text(
        json.dumps(options, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    new_job = JobRepository().create(
        filename=filename, input_path=input_path, output_dir=new_dir / "output", job_id=new_id
    )
    process_video_job.delay(new_job.id, options)
    st.rerun(scope="app")


def _render_job(job) -> None:
    with st.expander(
        f"{job.filename} - {status_label(job)} ({job.id[:8]})",
        icon=status_icon(job),
        expanded=job.status == JobStatus.RUNNING,
    ):
        if job.status in (JobStatus.QUEUED, JobStatus.RUNNING):
            render_stage_progress(job.stage)
        if job.error_message:
            st.warning(job.error_message)
        st.caption(f"Tạo lúc: {job.created_at} | Cập nhật: {job.updated_at}")

        if job.status == JobStatus.DONE:
            _render_results(job)

        st.divider()
        _render_rerun_button(job)
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
