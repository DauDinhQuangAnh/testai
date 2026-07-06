"""Test cac ham thuan trong downloader_ytdlp.py - khong goi yt-dlp/mang that."""

from subtitle_pipeline.infrastructure.downloader_ytdlp import (
    _cookie_options,
    friendly_yt_dlp_error,
)


def test_cookie_options_empty_when_env_unset(monkeypatch):
    monkeypatch.delenv("YTDLP_COOKIES_FILE", raising=False)

    assert _cookie_options() == {}


def test_cookie_options_empty_when_file_does_not_exist(monkeypatch, tmp_path):
    monkeypatch.setenv("YTDLP_COOKIES_FILE", str(tmp_path / "does-not-exist.txt"))

    assert _cookie_options() == {}


def test_cookie_options_returns_cookiefile_when_file_exists(monkeypatch, tmp_path):
    cookies_file = tmp_path / "cookies.txt"
    cookies_file.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
    monkeypatch.setenv("YTDLP_COOKIES_FILE", str(cookies_file))

    assert _cookie_options() == {"cookiefile": str(cookies_file)}


def test_friendly_error_detects_youtube_bot_check():
    message = friendly_yt_dlp_error("ERROR: [youtube] abc123: Sign in to confirm you're not a bot.")

    assert "Lam moi cookie" in message


def test_friendly_error_detects_cookies_are_needed_variant():
    message = friendly_yt_dlp_error("Fresh cookies (not necessarily logged in) are needed.")

    assert "Lam moi cookie" in message


def test_friendly_error_passes_through_unknown_message():
    assert friendly_yt_dlp_error("some other random error") == "some other random error"
