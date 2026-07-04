"""Test _build_download_command - ham thuan, khong goi yt-dlp that."""

from pathlib import Path

import pytest

from subtitle_pipeline.infrastructure.downloader_ytdlp import _build_download_command


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
