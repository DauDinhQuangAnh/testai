"""Trang upload: nguoi dung tai video/audio len, tao Job trong DB, enqueue Celery
task xu ly AI pipeline (Phase 2 - subtitle_pipeline). Chay qua: streamlit run
app/Home.py (Streamlit tu nap file nay tu thu muc app/pages/).

Kiem tra truoc khi tao job: (1) dinh dang file hop le, (2) kich thuoc file
khong vuot gioi han. Khong con chan theo usage/goi cuoc - du an la ca nhan,
khong thuong mai (xem HANDOFF.md, quyet dinh 2026-07-03 bo gioi han
Free/Pro).

Nguoi dung chon luon ngon ngu long tieng ngay tai day (thay vi phai vao Editor
bam them buoc rieng) - 1 job DUY NHAT se chay het transcribe -> dich -> long
tieng, ra video hoan chinh (xem HANDOFF.md Phase 5b, quyet dinh gop flow
2026-07-03). Trang Editor van giu nut thu cong de lam lai/doi ngon ngu khac
sau nay.
"""
import sys
import uuid
from pathlib import Path

import streamlit as st

for _parent in Path(__file__).resolve().parents:
    if (_parent / "pyproject.toml").exists():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from app.auth.streamlit_helpers import require_login
from app.config import AppConfig
from app.jobs.repository import JobRepository
from app.jobs.tasks import process_video_job
from subtitle_pipeline.infrastructure.translator_nllb import SUPPORTED_LANGUAGES

ALLOWED_EXTENSIONS = {"mp4", "mkv", "mov", "wav", "mp3", "m4a"}
MAX_FILE_SIZE_MB = 500

st.set_page_config(page_title="Upload - AI Subtitle Studio")
user = require_login()
st.title("Upload video/audio")

config = AppConfig.from_env()
job_repo = JobRepository()

uploaded_file = st.file_uploader(
    "Chon file video/audio", type=sorted(ALLOWED_EXTENSIONS)
)
target_language = st.selectbox(
    "Ngon ngu long tieng",
    SUPPORTED_LANGUAGES,
    index=SUPPORTED_LANGUAGES.index("vi") if "vi" in SUPPORTED_LANGUAGES else 0,
)

if uploaded_file is not None:
    extension = uploaded_file.name.rsplit(".", 1)[-1].lower()
    size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)

    if extension not in ALLOWED_EXTENSIONS:
        st.error(f"Dinh dang '.{extension}' khong duoc ho tro.")
        st.stop()
    if size_mb > MAX_FILE_SIZE_MB:
        st.error(f"File qua lon ({size_mb:.0f} MB), gioi han la {MAX_FILE_SIZE_MB} MB.")
        st.stop()

    if st.button("Tao job xu ly"):
        job_id = str(uuid.uuid4())
        job_dir = config.storage_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        input_path = job_dir / uploaded_file.name
        input_path.write_bytes(uploaded_file.getvalue())

        job = job_repo.create(
            filename=uploaded_file.name,
            input_path=input_path,
            output_dir=job_dir / "output",
            user_id=user.id,
            job_id=job_id,
        )
        process_video_job.delay(job.id, target_language)

        st.success(f"Da tao job `{job.id}`. Xem trang thai o trang Dashboard.")
        st.info(
            f"Job se tu chay het: tach am -> nhan dien loi noi -> dich sang "
            f"'{target_language}' -> long tieng -> xuat video hoan chinh, khong "
            f"can thao tac them. Can co Celery worker + Redis + Postgres dang "
            f"chay - xem HANDOFF.md muc Phase 3."
        )
