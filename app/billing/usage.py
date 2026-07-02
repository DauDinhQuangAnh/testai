"""Tinh usage (tong so phut da xu ly trong thang hien tai) de kiem tra gioi han
goi cuoc. Dung timestamp `end` cua segment cuoi cung trong file JSON ket qua
lam uoc luong thoi luong audio (khong can them dependency ffprobe rieng, vi du
lieu nay da co san tu ket qua pipeline).
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from app.db.models import Job, JobStatus


def monthly_minutes_used(jobs: list[Job], now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    total_seconds = sum(
        _segment_duration_seconds(job)
        for job in jobs
        if job.status == JobStatus.DONE
        and job.created_at.month == now.month
        and job.created_at.year == now.year
    )
    return total_seconds / 60.0


def _segment_duration_seconds(job: Job) -> float:
    json_path = Path(job.output_dir) / f"{Path(job.input_path).stem}.json"
    if not json_path.exists():
        return 0.0
    with open(json_path, encoding="utf-8") as f:
        segments = json.load(f)
    if not segments:
        return 0.0
    return max(seg["end"] for seg in segments)
