"""Small job-creation service used by non-web adapters.

The React/FastAPI upload flow can keep its current router behavior.  New
adapters, such as Telegram, call this module so they only enqueue a normal
pipeline job and do not touch the video-processing flow itself.
"""

import json
import uuid
from pathlib import Path
from typing import Any

from app.config import AppConfig
from app.jobs.tasks import process_video_job
from backend.db import job_repo
from subtitle_pipeline.infrastructure.downloader_ytdlp import sanitize_filename

DOWNLOAD_QUALITIES = {"best", "1080p", "720p", "480p"}


class JobCreationError(ValueError):
    pass


def default_download_job_options(
    url: str,
    *,
    title: str | None = None,
    quality: str = "best",
    target_language: str = "vi",
    source_language: str | None = None,
    trim_seconds: int | None = None,
) -> dict[str, Any]:
    """Return the same options shape used by the web wizard, for URL jobs."""
    return {
        "source": {
            "trim_seconds": trim_seconds,
            "source_language": source_language,
            "input_mode": "download",
            "download": {
                "url": url,
                "quality": quality,
                "title": title,
            },
        },
        "dubbing": {
            "enabled": True,
            "target_language": target_language,
            "voice": None,
            "rate_percent": 0,
            "pitch_hz": 0,
        },
        "translation": {
            "glossary": "",
            "pronunciation": "",
            "max_chars_per_line": 42,
            "max_lines": 2,
        },
        "subtitle": {
            "burn_in": False,
            "style": {
                "font": "Arial",
                "font_size": 48,
                "text_color": "#FFFFFF",
                "background_color": "#000000",
                "outline_width": 2,
                "position_x": 50,
                "position_y": 90,
                "opaque_box": False,
            },
        },
        "audio": {"original_volume": 0, "dub_volume": 1, "ducking": False},
        "output": {"format": "mp4", "quality": "balanced"},
    }


def write_job_config(job_dir: Path, options: dict[str, Any]) -> None:
    (job_dir / "job_config.json").write_text(
        json.dumps(options, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def create_download_job(
    *,
    url: str,
    title: str | None = None,
    quality: str = "best",
    user_id: str | None = None,
    options: dict[str, Any] | None = None,
    telegram: dict[str, Any] | None = None,
    enqueue_task=process_video_job,
    job_repo_factory=job_repo,
) -> str:
    """Create and enqueue a URL-based pipeline job.

    This intentionally returns only the job id.  Callers that need more detail
    can read the job from JobRepository, keeping this adapter surface tiny.

    Uses `backend.db.job_repo` (the same cached session-factory singleton the
    FastAPI backend uses) instead of instantiating `JobRepository()` directly
    - the latter calls `make_session_factory()` internally, which opens a
    brand new SQLAlchemy engine/connection pool on every call. Since the
    Telegram bot lives in a long-running polling loop and calls this once per
    confirmed download, that would leak a new unclosed pool per job.
    """
    if quality not in DOWNLOAD_QUALITIES:
        raise JobCreationError("Chat luong tai video khong hop le")
    if not url.strip():
        raise JobCreationError("Can URL video")

    job_id = str(uuid.uuid4())
    job_dir = AppConfig.from_env().storage_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{sanitize_filename(title or 'downloaded-video')}.mp4"
    input_path = job_dir / filename

    job_options = options or default_download_job_options(url, title=title, quality=quality)
    source = job_options.setdefault("source", {})
    source["input_mode"] = "download"
    source["download"] = {"url": url, "quality": quality, "title": title}
    if telegram:
        job_options["telegram"] = telegram

    write_job_config(job_dir, job_options)
    job_repo_factory().create(
        filename=filename,
        input_path=input_path,
        output_dir=job_dir / "output",
        job_id=job_id,
        user_id=user_id,
    )
    enqueue_task.delay(job_id, job_options)
    return job_id
