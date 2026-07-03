"""Helper UI dung chung cho cac trang Streamlit: anh xa `Job.stage` (ghi boi
Celery task, xem app/jobs/tasks.py) sang nhan tieng Viet + phan tram tien do
de Dashboard/Editor hien progress bar nhat quan.
"""

from app.db.models import Job, JobStatus

# Thu tu stage khop voi thu tu notify() trong TranscriptionPipeline.run() +
# 2 giai doan translate/dub cua process_video_job. Tien do = vi tri/len.
PIPELINE_STAGES: list[tuple[str, str]] = [
    ("starting", "Khoi dong"),
    ("extract_audio", "Tach audio"),
    ("denoise", "Khu on"),
    ("transcribe", "Nhan dien loi noi"),
    ("align", "Can chinh thoi gian"),
    ("diarize", "Nhan dien nguoi noi"),
    ("merge", "Ghep ket qua"),
    ("translate", "Dich"),
    ("dub", "Long tieng"),
    ("done", "Hoan thanh"),
]

# Stage phu phat sinh tu nhanh fallback/bo qua - hien thi nhu stage goc.
_STAGE_ALIASES = {
    "align_fallback_no_model": "align",
    "translate_dub_skipped": "dub",
}

_STATUS_LABELS = {
    JobStatus.QUEUED: "Dang cho",
    JobStatus.RUNNING: "Dang chay",
    JobStatus.DONE: "Hoan thanh",
    JobStatus.FAILED: "That bai",
}

_STATUS_ICONS = {
    JobStatus.QUEUED: ":material/schedule:",
    JobStatus.RUNNING: ":material/autorenew:",
    JobStatus.DONE: ":material/check_circle:",
    JobStatus.FAILED: ":material/error:",
}


def stage_progress(stage: str | None) -> tuple[float, str]:
    """Tra ve (ty le 0..1, nhan tieng Viet) cho progress bar."""
    if not stage:
        return 0.0, "Dang cho xu ly"
    stage = _STAGE_ALIASES.get(stage, stage)
    for index, (name, label) in enumerate(PIPELINE_STAGES):
        if name == stage:
            return (index + 1) / len(PIPELINE_STAGES), label
    return 0.0, stage


def status_label(job: Job) -> str:
    return _STATUS_LABELS.get(job.status, job.status.value)


def status_icon(job: Job) -> str:
    return _STATUS_ICONS.get(job.status, ":material/help:")
