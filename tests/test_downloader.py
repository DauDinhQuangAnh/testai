"""Test _build_download_command - ham thuan, khong goi yt-dlp that."""

from pathlib import Path

import pytest

from subtitle_pipeline.infrastructure.downloader_ytdlp import (
    _build_download_command,
    _format_download_error,
    _normalize_url,
)


def test_command_uses_venv_python_module_and_url():
    cmd = _build_download_command("https://youtu.be/abc", Path("jobdir"), "720p")

    assert cmd[1:3] == ["-m", "yt_dlp"]
    assert cmd[-1] == "https://youtu.be/abc"
    assert "--no-playlist" in cmd


def test_720p_quality_limits_height():
    cmd = _build_download_command("https://youtu.be/abc", Path("jobdir"), "720p")

    fmt = cmd[cmd.index("-f") + 1]
    assert "height<=720" in fmt


def test_best_quality_has_no_height_limit():
    cmd = _build_download_command("https://youtu.be/abc", Path("jobdir"), "best")

    fmt = cmd[cmd.index("-f") + 1]
    assert "height" not in fmt


def test_unknown_quality_raises():
    with pytest.raises(ValueError):
        _build_download_command("https://youtu.be/abc", Path("jobdir"), "4k")


def test_command_can_use_cookies_file(monkeypatch):
    monkeypatch.setenv("YTDLP_COOKIES_FILE", "cookies.txt")

    cmd = _build_download_command("https://youtu.be/abc", Path("jobdir"), "720p")

    assert cmd[cmd.index("--cookies") + 1] == "cookies.txt"


def test_command_can_use_cookies_from_browser(monkeypatch):
    monkeypatch.delenv("YTDLP_COOKIES_FILE", raising=False)
    monkeypatch.setenv("YTDLP_COOKIES_FROM_BROWSER", "edge")

    cmd = _build_download_command("https://youtu.be/abc", Path("jobdir"), "720p")

    assert cmd[cmd.index("--cookies-from-browser") + 1] == "edge"


def test_normalize_url_rewrites_douyin_modal_id_to_video_path():
    url = "https://www.douyin.com/jingxuan?modal_id=7656195869917728041"

    assert _normalize_url(url) == "https://www.douyin.com/video/7656195869917728041"


def test_normalize_url_leaves_standard_douyin_video_url_unchanged():
    url = "https://www.douyin.com/video/7656195869917728041"

    assert _normalize_url(url) == url


def test_normalize_url_leaves_non_douyin_url_unchanged():
    url = "https://youtu.be/abc?modal_id=123"

    assert _normalize_url(url) == url


def test_build_command_normalizes_douyin_modal_id_url():
    cmd = _build_download_command(
        "https://www.douyin.com/jingxuan?modal_id=7656195869917728041",
        Path("jobdir"),
        "720p",
    )

    assert cmd[-1] == "https://www.douyin.com/video/7656195869917728041"


class _FakeProcessError:
    def __init__(self, stderr: str = "", stdout: str = ""):
        self.stderr = stderr
        self.stdout = stdout

    def __str__(self) -> str:
        return "process failed"


def test_format_error_detects_youtube_bot_block():
    exc = _FakeProcessError(stderr="ERROR: Sign in to confirm you're not a bot")

    message = _format_download_error(exc)

    assert "YTDLP_COOKIES_FILE" in message


def test_format_error_detects_douyin_cookie_requirement():
    exc = _FakeProcessError(stderr="ERROR: Fresh cookies (not necessarily logged in) are needed")

    message = _format_download_error(exc)

    assert "Douyin" in message
    assert "YTDLP_COOKIES_FILE" in message
