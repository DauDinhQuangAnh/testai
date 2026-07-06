import os
from pathlib import Path
from urllib.parse import quote

from app.db.models import Job
from backend.email_sender import EmailNotConfiguredError, send_direct_download_email
from backend.share_links import create_file_share_token

from .client import TelegramClient, TelegramNotConfiguredError

VIDEO_SUFFIXES = {".mp4", ".mkv", ".mov", ".webm"}


def _backend_public_url() -> str:
    return os.environ.get(
        "BACKEND_PUBLIC_URL",
        os.environ.get("BACKEND_URL", "http://localhost:8000"),
    ).rstrip("/")


def _share_ttl_seconds() -> int:
    return int(os.environ.get("PUBLIC_LINK_TTL_SECONDS", str(7 * 24 * 60 * 60)))


def _find_result_video(job: Job) -> Path | None:
    output_dir = Path(job.output_dir)
    if not output_dir.exists():
        return None
    videos = [
        path
        for path in output_dir.glob("*.*")
        if path.is_file() and ".dubbed." in path.name and path.suffix.lower() in VIDEO_SUFFIXES
    ]
    if not videos:
        return None
    return max(videos, key=lambda path: path.stat().st_size)


def _download_url(job_id: str, filename: str) -> str:
    token = create_file_share_token(job_id, filename, ttl_seconds=_share_ttl_seconds())
    path = f"/api/public/jobs/{job_id}/files/{quote(filename)}"
    return f"{_backend_public_url()}{path}?token={quote(token)}"


def notify_telegram_job_done(job: Job, options: dict) -> None:
    telegram = options.get("telegram") or {}
    chat_id = telegram.get("chat_id")
    if not chat_id:
        return

    try:
        client = TelegramClient()
    except TelegramNotConfiguredError:
        return

    result = _find_result_video(job)
    if result is None:
        client.send_message(
            chat_id,
            "Job da xong, nhung chua tim thay file video long tieng de gui link tai.",
        )
        return

    url = _download_url(job.id, result.name)
    notify_email = (telegram.get("notify_email") or "").strip()
    if notify_email:
        try:
            send_direct_download_email(notify_email, result.name, url)
            client.send_message(
                chat_id,
                f"Video da xu ly xong. Minh da gui link tai qua email: {notify_email}",
            )
        except EmailNotConfiguredError as exc:
            client.send_message(
                chat_id,
                "Video da xu ly xong nhung email chua duoc cau hinh.\n"
                f"Link tai: {url}\n\nChi tiet: {exc}",
            )
        except Exception as exc:
            client.send_message(
                chat_id,
                f"Video da xu ly xong nhung gui email that bai: {exc}\nLink tai: {url}",
            )
        return

    client.send_message(chat_id, f"Video da xu ly xong.\nLink tai: {url}")


def notify_telegram_job_failed(job: Job, options: dict, error_message: str) -> None:
    telegram = options.get("telegram") or {}
    chat_id = telegram.get("chat_id")
    if not chat_id:
        return
    try:
        TelegramClient().send_message(chat_id, f"Job xu ly that bai:\n{error_message}")
    except TelegramNotConfiguredError:
        return
