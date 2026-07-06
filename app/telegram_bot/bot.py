"""Telegram polling runner.

Run with:
    python -m app.telegram_bot.bot

This process is optional and isolated.  It creates ordinary download jobs via
app.jobs.service, then Celery completion notification sends the final link.
"""

import os
import re
import time
from typing import Any

from dotenv import load_dotenv

from app.jobs.service import create_download_job, default_download_job_options
from subtitle_pipeline.infrastructure.downloader_ytdlp import analyze_video

from .client import TelegramClient

load_dotenv()

URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _allowed_chat_ids() -> set[int]:
    raw = os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS", "").strip()
    if not raw:
        return set()
    return {int(part.strip()) for part in raw.split(",") if part.strip()}


def _default_quality() -> str:
    return os.environ.get("TELEGRAM_DEFAULT_QUALITY", "best")


def _target_language() -> str:
    return os.environ.get("TELEGRAM_TARGET_LANGUAGE", "vi")


def _trim_seconds() -> int | None:
    raw = os.environ.get("TELEGRAM_TRIM_SECONDS", "").strip()
    return int(raw) if raw else None


def _source_language() -> str | None:
    return os.environ.get("TELEGRAM_SOURCE_LANGUAGE", "").strip() or None


class TelegramJobBot:
    def __init__(self):
        self.client = TelegramClient()
        self.pending: dict[int, dict[str, Any]] = {}
        self.allowed = _allowed_chat_ids()

    def run_forever(self) -> None:
        offset = 0
        startup_chat_id = os.environ.get("TELEGRAM_STARTUP_CHAT_ID", "")
        if startup_chat_id:
            self.client.send_message(startup_chat_id, "VietDub Telegram bot da san sang.")

        while True:
            try:
                updates = self.client.request(
                    "getUpdates",
                    {
                        "offset": offset,
                        "timeout": 25,
                        "allowed_updates": ["message", "callback_query"],
                    },
                    timeout=35,
                )
                for update in updates:
                    offset = max(offset, int(update["update_id"]) + 1)
                    self.handle_update(update)
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                print(f"[telegram] polling error: {exc}", flush=True)
                time.sleep(5)

    def _is_allowed(self, chat_id: int) -> bool:
        return not self.allowed or chat_id in self.allowed

    def handle_update(self, update: dict[str, Any]) -> None:
        if "callback_query" in update:
            self.handle_callback(update["callback_query"])
            return

        message = update.get("message") or {}
        chat = message.get("chat") or {}
        chat_id = int(chat.get("id"))
        if not self._is_allowed(chat_id):
            self.client.send_message(chat_id, "Chat nay chua duoc phep dung bot.")
            return

        text = (message.get("text") or "").strip()
        if text in {"/start", "/help"}:
            self.client.send_message(
                chat_id,
                "Gui minh link YouTube/Douyin. Minh se hoi ban muon gui email "
                "hay nhan link tai trong bot.",
            )
            return
        if text == "/cancel":
            self.pending.pop(chat_id, None)
            self.client.send_message(chat_id, "Da huy thao tac dang cho.")
            return

        pending = self.pending.get(chat_id)
        if pending and pending.get("state") == "awaiting_email":
            self.handle_email(chat_id, text)
            return

        match = URL_RE.search(text)
        if not match:
            self.client.send_message(chat_id, "Hay gui mot link video hop le.")
            return
        self.handle_url(chat_id, match.group(0).rstrip(").,]"))

    def handle_url(self, chat_id: int, url: str) -> None:
        self.client.send_message(chat_id, "Minh dang doc thong tin video...")
        try:
            metadata = analyze_video(url)
        except Exception as exc:
            self.client.send_message(chat_id, f"Khong doc duoc link nay:\n{exc}")
            return

        quality = _default_quality()
        if not any(item.id == quality for item in metadata.qualities):
            quality = metadata.qualities[0].id if metadata.qualities else "best"

        self.pending[chat_id] = {
            "state": "choose_delivery",
            "url": metadata.url,
            "title": metadata.title,
            "quality": quality,
        }
        self.client.send_message(
            chat_id,
            f"Da nhan: {metadata.title}\nBan co muon gui ket qua qua email khong?",
            reply_markup={
                "inline_keyboard": [
                    [
                        {"text": "Co, gui email", "callback_data": "delivery_email"},
                        {"text": "Khong, gui link", "callback_data": "delivery_link"},
                    ]
                ]
            },
        )

    def handle_callback(self, callback: dict[str, Any]) -> None:
        message = callback.get("message") or {}
        chat_id = int((message.get("chat") or {}).get("id"))
        if not self._is_allowed(chat_id):
            self.client.answer_callback_query(callback["id"], "Chat chua duoc phep")
            return

        data = callback.get("data")
        self.client.answer_callback_query(callback["id"])
        pending = self.pending.get(chat_id)
        if not pending:
            self.client.send_message(chat_id, "Lua chon nay da het han. Gui lai link giup minh.")
            return

        if data == "delivery_email":
            pending["state"] = "awaiting_email"
            self.client.send_message(chat_id, "Nhap email nhan ket qua:")
            return
        if data == "delivery_link":
            self.create_job(chat_id, pending)
            return

    def handle_email(self, chat_id: int, text: str) -> None:
        email = text.strip()
        if not EMAIL_RE.match(email):
            self.client.send_message(chat_id, "Email chua dung dinh dang. Nhap lai hoac /cancel.")
            return
        pending = self.pending.get(chat_id)
        if not pending:
            self.client.send_message(chat_id, "Phien da het han. Gui lai link giup minh.")
            return
        pending["notify_email"] = email
        self.create_job(chat_id, pending)

    def create_job(self, chat_id: int, pending: dict[str, Any]) -> None:
        options = default_download_job_options(
            pending["url"],
            title=pending.get("title"),
            quality=pending.get("quality", "best"),
            target_language=_target_language(),
            source_language=_source_language(),
            trim_seconds=_trim_seconds(),
        )
        telegram = {
            "chat_id": chat_id,
            "notify_email": pending.get("notify_email"),
        }
        try:
            job_id = create_download_job(
                url=pending["url"],
                title=pending.get("title"),
                quality=pending.get("quality", "best"),
                options=options,
                telegram=telegram,
            )
        except Exception as exc:
            self.client.send_message(chat_id, f"Tao job that bai:\n{exc}")
            return

        self.pending.pop(chat_id, None)
        self.client.send_message(
            chat_id,
            f"Da tao job {job_id}.\nMinh se bao lai khi xu ly xong.",
        )


def main() -> None:
    TelegramJobBot().run_forever()


if __name__ == "__main__":
    main()
