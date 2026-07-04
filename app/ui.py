"""Helper UI dung chung cho cac trang Streamlit: anh xa `Job.stage` (ghi boi
Celery task, xem app/jobs/tasks.py) sang nhan tieng Viet + phan tram tien do
de Dashboard/Editor hien progress bar nhat quan.
"""

import streamlit as st

from app.db.models import Job, JobStatus

# Thu tu stage khop voi thu tu notify() trong TranscriptionPipeline.run() +
# 2 giai doan translate/dub cua process_video_job. Tien do = vi tri/len.
PIPELINE_STAGES: list[tuple[str, str]] = [
    ("starting", "Khởi động"),
    ("download", "Tải video từ URL"),
    ("extract_audio", "Tách audio"),
    ("denoise", "Khử ồn"),
    ("transcribe", "Nhận diện lời nói"),
    ("align", "Căn chỉnh thời gian"),
    ("diarize", "Nhận diện người nói"),
    ("merge", "Ghép kết quả"),
    ("translate", "Dịch"),
    ("dub", "Lồng tiếng"),
    ("done", "Hoàn thành"),
]

# Stage phu phat sinh tu nhanh fallback/bo qua - hien thi nhu stage goc.
_STAGE_ALIASES = {
    "align_fallback_no_model": "align",
    "translate_dub_skipped": "dub",
}

_STATUS_LABELS = {
    JobStatus.QUEUED: "Đang chờ",
    JobStatus.RUNNING: "Đang chạy",
    JobStatus.DONE: "Hoàn thành",
    JobStatus.FAILED: "Thất bại",
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
        return 0.0, "Đang chờ xử lý"
    stage = _STAGE_ALIASES.get(stage, stage)
    for index, (name, label) in enumerate(PIPELINE_STAGES):
        if name == stage:
            return (index + 1) / len(PIPELINE_STAGES), label
    return 0.0, stage


def status_label(job: Job) -> str:
    return _STATUS_LABELS.get(job.status, job.status.value)


def status_icon(job: Job) -> str:
    return _STATUS_ICONS.get(job.status, ":material/help:")


def render_stage_progress(stage: str | None) -> None:
    """Ve thanh tien do dang nhieu segment (1 o mau/buoc pipeline) thay cho
    1 thanh `st.progress()` don - de nguoi dung thay ro dang o buoc nao
    trong tong so buoc, buoc hien tai co hieu ung nhap nhay (dang chay).
    Dung HTML/CSS inline vi Streamlit khong co widget stepper san - mau lay
    tu `.streamlit/config.toml` (primaryColor) de dong bo theme.
    """
    resolved_stage = _STAGE_ALIASES.get(stage, stage) if stage else None
    current_index = next(
        (i for i, (name, _label) in enumerate(PIPELINE_STAGES) if name == resolved_stage), -1
    )

    segments = []
    for i in range(len(PIPELINE_STAGES)):
        if i < current_index:
            css_class = "stage-done"
        elif i == current_index:
            css_class = "stage-current"
        else:
            css_class = "stage-pending"
        label = PIPELINE_STAGES[i][1]
        segments.append(f'<div class="stage-segment {css_class}" title="{label}"></div>')

    _fraction, current_label = stage_progress(stage)
    total = len(PIPELINE_STAGES)
    percent = round(((current_index + 1) / total) * 100) if current_index >= 0 else 0
    caption = f"<span>Bước hiện tại: {current_label}</span><span>{percent}%</span>"

    st.markdown(
        f"""
        <style>
        .stage-bar {{ display: flex; gap: 4px; margin: 10px 0 6px 0; }}
        .stage-segment {{
            flex: 1; height: 8px; border-radius: 4px;
            background: #E4E7F0; transition: background 0.4s ease;
        }}
        .stage-segment.stage-done {{ background: #4C6FFF; }}
        .stage-segment.stage-current {{
            background: #4C6FFF;
            animation: stage-pulse 1.2s ease-in-out infinite;
        }}
        @keyframes stage-pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.35; }}
        }}
        .stage-caption {{
            font-size: 0.85rem; color: #6B7280; display: flex;
            justify-content: space-between;
        }}
        </style>
        <div class="stage-bar">{"".join(segments)}</div>
        <div class="stage-caption">{caption}</div>
        """,
        unsafe_allow_html=True,
    )
