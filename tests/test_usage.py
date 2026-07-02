"""Test monthly_minutes_used - logic thuan doc file JSON tam, khong can DB that."""
import json
from datetime import datetime, timezone
from pathlib import Path

from app.billing.usage import monthly_minutes_used
from app.db.models import Job, JobStatus


def _make_job(
    tmp_path: Path, stem: str, segments: list[dict], status=JobStatus.DONE, **kwargs
) -> Job:
    output_dir = tmp_path / stem
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / f"{stem}.json", "w", encoding="utf-8") as f:
        json.dump(segments, f)

    return Job(
        id=stem,
        user_id="user-1",
        filename=f"{stem}.mp4",
        input_path=str(tmp_path / f"{stem}.mp4"),
        output_dir=str(output_dir),
        status=status,
        created_at=kwargs.get("created_at", datetime.now(timezone.utc)),
    )


def test_sums_duration_of_done_jobs_this_month(tmp_path):
    now = datetime.now(timezone.utc)
    job = _make_job(tmp_path, "job1", [{"start": 0.0, "end": 90.0, "text": "hi"}], created_at=now)

    minutes = monthly_minutes_used([job], now=now)

    assert minutes == 1.5


def test_ignores_jobs_not_done(tmp_path):
    now = datetime.now(timezone.utc)
    job = _make_job(
        tmp_path, "job2", [{"start": 0.0, "end": 60.0, "text": "hi"}],
        status=JobStatus.FAILED, created_at=now,
    )

    minutes = monthly_minutes_used([job], now=now)

    assert minutes == 0.0


def test_ignores_jobs_from_other_months(tmp_path):
    now = datetime.now(timezone.utc)
    last_month = now.replace(month=1 if now.month != 1 else 2, day=1)
    job = _make_job(
        tmp_path, "job3", [{"start": 0.0, "end": 60.0, "text": "hi"}], created_at=last_month
    )

    minutes = monthly_minutes_used([job], now=now)

    assert minutes == 0.0
