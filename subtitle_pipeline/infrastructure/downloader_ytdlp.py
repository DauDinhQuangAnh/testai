"""Download URL sources with yt-dlp.

The worker downloads URL-based jobs into the job directory before running the
AI pipeline. Some YouTube AND Douyin requests require browser cookies when
the site blocks anonymous/bot traffic; configure this through environment
variables (cookies.txt can hold cookies for multiple domains at once):

- YTDLP_COOKIES_FILE=path/to/cookies.txt
- YTDLP_COOKIES_FROM_BROWSER=chrome|edge|firefox
"""

import os
import re
import subprocess
import sys
from pathlib import Path

QUALITY_FORMATS = {
    "720p": "bv*[height<=720]+ba/b[height<=720]/b",
    "best": "bv*+ba/b",
}

# Link chia se tu app Douyin (vd. mo tu tab "jingxuan"/"discover" cho video
# trong 1 modal) dang "douyin.com/jingxuan?modal_id=<id>" - yt-dlp KHONG
# nhan dien duoc dang nay (bao "Unsupported URL", roi ve generic extractor),
# chi nhan dien dang chuan "douyin.com/video/<id>". Doi ve dang chuan truoc
# khi goi yt-dlp.
_DOUYIN_MODAL_ID_RE = re.compile(r"modal_id=(\d+)")


def _normalize_url(url: str) -> str:
    if "douyin.com" in url:
        match = _DOUYIN_MODAL_ID_RE.search(url)
        if match:
            return f"https://www.douyin.com/video/{match.group(1)}"
    return url


def _yt_dlp_cookie_args() -> list[str]:
    cookies_file = os.environ.get("YTDLP_COOKIES_FILE", "").strip()
    if cookies_file:
        return ["--cookies", cookies_file]

    cookies_from_browser = os.environ.get("YTDLP_COOKIES_FROM_BROWSER", "").strip()
    if cookies_from_browser:
        return ["--cookies-from-browser", cookies_from_browser]

    return []


def _build_download_command(url: str, out_dir: Path, quality: str) -> list[str]:
    if quality not in QUALITY_FORMATS:
        raise ValueError(f"Chat luong tai chua ho tro: {quality}")

    return [
        sys.executable,
        "-m",
        "yt_dlp",
        "--no-playlist",
        *_yt_dlp_cookie_args(),
        "--restrict-filenames",
        "-o",
        str(out_dir / "%(title).80s.%(ext)s"),
        "-f",
        QUALITY_FORMATS[quality],
        "--merge-output-format",
        "mp4",
        _normalize_url(url),
    ]


def _format_download_error(exc: subprocess.CalledProcessError) -> str:
    output = "\n".join(part for part in [exc.stderr, exc.stdout] if part).strip()
    if not output:
        output = str(exc)

    lines = [line.strip() for line in output.splitlines() if line.strip()]
    important = [
        line
        for line in lines
        if line.startswith("ERROR:")
        or "Sign in to confirm" in line
        or "HTTP Error 429" in line
        or "cookies" in line.lower()
    ]
    message = "\n".join(important[-6:] or lines[-8:])
    if "Sign in to confirm" in message or "HTTP Error 429" in message or "not a bot" in message:
        return (
            "YouTube dang chan bot/IP nen khong tai duoc video. "
            "Hay export cookies YouTube tu trinh duyet dang dang nhap thanh cookies.txt, "
            "roi cau hinh YTDLP_COOKIES_FILE trong .env."
        )
    if "fresh cookies" in message.lower() or "cookies are needed" in message.lower():
        return (
            "Douyin can cookie dang nhap moi de tai video nay. "
            "Hay export cookie tu douyin.com (dang dang nhap) vao CUNG file cookies.txt "
            "da cau hinh o YTDLP_COOKIES_FILE (gop chung voi cookie YouTube trong 1 file "
            "duoc, khong can file rieng)."
        )
    return message


def download_video(url: str, out_dir: Path, quality: str = "720p") -> Path:
    """Download a URL into out_dir and return the downloaded file path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    before = set(out_dir.iterdir())
    cmd = _build_download_command(url, out_dir, quality)
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(_format_download_error(exc)) from exc

    new_files = [p for p in out_dir.iterdir() if p.is_file() and p not in before]
    if not new_files:
        raise RuntimeError(f"yt-dlp finished but no downloaded file was found in {out_dir}")
    return max(new_files, key=lambda p: p.stat().st_size)
