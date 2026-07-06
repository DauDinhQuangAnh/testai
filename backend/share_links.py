"""Signed one-file download links for external channels such as Telegram."""

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any


class ShareLinkError(ValueError):
    pass


def _secret() -> bytes:
    return os.environ.get(
        "PUBLIC_LINK_SECRET",
        os.environ.get("SESSION_SECRET_KEY", "dev-secret-doi-khi-deploy"),
    ).encode("utf-8")


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(body: str) -> str:
    digest = hmac.new(_secret(), body.encode("ascii"), hashlib.sha256).digest()
    return _b64_encode(digest)


def create_file_share_token(job_id: str, filename: str, *, ttl_seconds: int = 86400) -> str:
    payload = {
        "job_id": job_id,
        "filename": filename,
        "exp": int(time.time()) + ttl_seconds,
    }
    body = _b64_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    return f"{body}.{_sign(body)}"


def verify_file_share_token(token: str, *, job_id: str, filename: str) -> dict[str, Any]:
    try:
        body, signature = token.split(".", 1)
    except ValueError as exc:
        raise ShareLinkError("Token tai file khong hop le") from exc

    expected = _sign(body)
    if not hmac.compare_digest(signature, expected):
        raise ShareLinkError("Token tai file khong hop le")

    try:
        payload = json.loads(_b64_decode(body).decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise ShareLinkError("Token tai file khong hop le") from exc

    if payload.get("job_id") != job_id or payload.get("filename") != filename:
        raise ShareLinkError("Token tai file khong khop")
    if int(payload.get("exp", 0)) < int(time.time()):
        raise ShareLinkError("Token tai file da het han")
    return payload
