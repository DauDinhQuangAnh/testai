"""Trang upload: nguoi dung tai video/audio len, tao Job trong DB, enqueue Celery
task xu ly AI pipeline (Phase 2 - subtitle_pipeline). Chay qua: streamlit run
app/Home.py (Streamlit tu nap file nay tu thu muc app/pages/).

Kiem tra truoc khi tao job: (1) dinh dang file hop le, (2) kich thuoc file
khong vuot gioi han, (3) usage thang nay chua vuot gioi han goi cuoc - xem
app/billing/.
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
from app.billing.plans import PLAN_CATALOG
from app.billing.repository import SubscriptionRepository
from app.billing.usage import monthly_minutes_used
from app.config import AppConfig
from app.db.models import PlanTier
from app.jobs.repository import JobRepository
from app.jobs.tasks import process_video_job

ALLOWED_EXTENSIONS = {"mp4", "mkv", "mov", "wav", "mp3", "m4a"}
MAX_FILE_SIZE_MB = 500

st.set_page_config(page_title="Upload - AI Subtitle Studio")
user = require_login()
st.title("Upload video/audio")

config = AppConfig.from_env()
job_repo = JobRepository()

subscription = SubscriptionRepository().get_by_user(user.id)
current_plan = subscription.plan if subscription else PlanTier.FREE
plan_info = PLAN_CATALOG[current_plan]
minutes_used = monthly_minutes_used(job_repo.list_by_user(user.id))

if minutes_used >= plan_info.monthly_minutes_limit:
    st.error(
        f"Ban da dung het {plan_info.monthly_minutes_limit:.0f} phut/thang cua goi "
        f"{plan_info.name}. Vao trang Billing de nang cap goi."
    )
    st.stop()

uploaded_file = st.file_uploader(
    "Chon file video/audio", type=sorted(ALLOWED_EXTENSIONS)
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
        process_video_job.delay(job.id)

        st.success(f"Da tao job `{job.id}`. Xem trang thai o trang Dashboard.")
        st.info(
            "Luu y: can co Celery worker + Redis + Postgres dang chay de job duoc "
            "xu ly - xem HANDOFF.md muc Phase 3."
        )
