import json
import os
from typing import Any
from urllib import request


class TelegramNotConfiguredError(RuntimeError):
    pass


class TelegramClient:
    def __init__(self, token: str | None = None):
        self.token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if not self.token:
            raise TelegramNotConfiguredError("TELEGRAM_BOT_TOKEN is not configured")

    def request(self, method: str, payload: dict[str, Any] | None = None, *, timeout: int = 30):
        url = f"https://api.telegram.org/bot{self.token}/{method}"
        data = json.dumps(payload or {}).encode("utf-8")
        req = request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        if not body.get("ok"):
            raise RuntimeError(body.get("description") or f"Telegram method {method} failed")
        return body.get("result")

    def send_message(
        self,
        chat_id: int | str,
        text: str,
        *,
        reply_markup: dict[str, Any] | None = None,
        disable_web_page_preview: bool = True,
    ) -> None:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": disable_web_page_preview,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        self.request("sendMessage", payload)

    def answer_callback_query(self, callback_query_id: str, text: str = "") -> None:
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        self.request("answerCallbackQuery", payload)
