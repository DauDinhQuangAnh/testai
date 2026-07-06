"""Anh xa `Job.stage` (ghi boi Celery task, xem app/jobs/tasks.py) sang nhan
tieng Viet + phan tram tien do. Dung boi `backend/schemas.py` (JobOut) - FE
React (frontend/) hien lai qua StageProgress.tsx.
"""

# Thu tu stage khop voi thu tu notify() trong TranscriptionPipeline.run() +
# cac giai doan translate/dub cua process_video_job. Tien do = vi tri/len.
PIPELINE_STAGES: list[tuple[str, str]] = [
    ("starting", "Khởi động"),
    ("download", "Tải video"),
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
STAGE_ALIASES = {
    "align_fallback_no_model": "align",
    "translate_dub_skipped": "dub",
}


def stage_progress(stage: str | None) -> tuple[float, str]:
    """Tra ve (ty le 0..1, nhan tieng Viet) cho progress bar."""
    if not stage:
        return 0.0, "Đang chờ xử lý"
    stage = STAGE_ALIASES.get(stage, stage)
    for index, (name, label) in enumerate(PIPELINE_STAGES):
        if name == stage:
            return (index + 1) / len(PIPELINE_STAGES), label
    return 0.0, stage
