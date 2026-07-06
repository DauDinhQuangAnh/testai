"""Small yt-dlp wrapper used by the web upload wizard.

The API creates a normal pipeline job from either an uploaded file or a public
video URL. URL jobs download into the job folder first, then the rest of the
pipeline reads the downloaded file exactly like an uploaded input.

YouTube thinh thoang chan request an danh voi loi "Sign in to confirm you're
not a bot" (yeu cau cookie tu 1 phien dang nhap that). Neu bien moi truong
`YTDLP_COOKIES_FILE` tro toi 1 file cookies.txt ton tai (sinh boi
`subtitle_pipeline/infrastructure/cookie_refresh.py`, xem nut "Lam moi
cookie" trong trang Admin), file do duoc truyen vao yt-dlp qua `cookiefile`
cho CA `analyze_video()` lan `download_video()`.
"""

from __future__ import annotations

import os
import re
import shutil
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

QUALITY_FORMATS = {
    "best": "bestvideo+bestaudio/best",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
}

QUALITY_FALLBACKS = {
    "best": [
        "bestvideo+bestaudio/best",
        "best[ext=mp4]/best",
        "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "best[height<=720]/best",
    ],
    "1080p": [
        "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "best[height<=1080]/best",
        "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "best[height<=720]/best",
    ],
    "720p": [
        "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "best[height<=720]/best",
        "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "best[height<=480]/best",
    ],
    "480p": [
        "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "best[height<=480]/best",
        "worst[ext=mp4]/worst",
    ],
}

QUALITY_LABELS = {
    "best": "Tot nhat",
    "1080p": "1080p",
    "720p": "720p",
    "480p": "480p",
}


@dataclass(frozen=True)
class QualityOption:
    id: str
    label: str
    format: str


@dataclass(frozen=True)
class VideoMetadata:
    url: str
    title: str
    thumbnail: str | None
    duration: int | None
    uploader: str | None
    source: str | None
    qualities: list[QualityOption]


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned[:150] or "downloaded-video"


def normalize_video_url(url: str) -> str:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    if "youtube.com" not in host:
        return url.strip()

    query = parse_qs(parsed.query)
    video_id = query.get("v", [None])[0]
    if not video_id:
        return url.strip()

    clean_query = urlencode({"v": video_id})
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", clean_query, ""))


def check_ffmpeg() -> str | None:
    missing = [name for name in ("ffmpeg", "ffprobe") if not shutil.which(name)]
    if missing:
        return "FFmpeg/FFprobe chua co trong PATH, khong the ghep stream video tai ve."
    return None


def _cookie_options() -> dict[str, str]:
    """Doc `YTDLP_COOKIES_FILE` tu env - tra ve `{"cookiefile": ...}` neu file
    ton tai, nguoc lai `{}` (yt-dlp se chay an danh, co the bi YouTube chan).
    """
    cookies_file = os.environ.get("YTDLP_COOKIES_FILE", "").strip()
    if cookies_file and Path(cookies_file).exists():
        return {"cookiefile": cookies_file}
    return {}


def friendly_yt_dlp_error(message: str) -> str:
    lower = message.lower()
    if (
        "sign in to confirm" in lower
        or "not a bot" in lower
        or "fresh cookies" in lower
        or "cookies are needed" in lower
    ):
        return (
            "YouTube yeu cau xac thuc (nghi ngo bot) nen khong doc/tai duoc video nay. "
            'Vao trang Admin, bam "Lam moi cookie" (can chay setup dang nhap 1 lan truoc, '
            "xem huong dan trong .env.example) roi thu lai."
        )
    if "unsupported url" in lower:
        return "Link nay chua duoc yt-dlp ho tro."
    if "private" in lower:
        return "Video dang private hoac khong the truy cap cong khai."
    if "http error 403" in lower or "forbidden" in lower:
        return "Nguon video tu choi stream nay. Hay thu lai hoac chon 720p/480p."
    if any(
        marker in lower
        for marker in (
            "unable to extract",
            "signature",
            "player response",
            "please report this issue",
            "updating yt-dlp",
        )
    ):
        return "yt-dlp khong doc duoc video nay; co the can cap nhat yt-dlp."
    return message


def analyze_video(url: str) -> VideoMetadata:
    import yt_dlp

    normalized = normalize_video_url(url)
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        **_cookie_options(),
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(normalized, download=False)
    except Exception as exc:
        raise RuntimeError(friendly_yt_dlp_error(str(exc))) from exc

    if info is None:
        raise RuntimeError("Khong doc duoc metadata video.")

    formats = info.get("formats") or []
    heights = {
        fmt.get("height")
        for fmt in formats
        if fmt.get("vcodec") not in (None, "none") and isinstance(fmt.get("height"), int)
    }
    max_height = max(heights) if heights else None

    qualities = [QualityOption("best", QUALITY_LABELS["best"], QUALITY_FORMATS["best"])]
    for quality_id, height in (("1080p", 1080), ("720p", 720), ("480p", 480)):
        if max_height and max_height >= height:
            qualities.append(
                QualityOption(quality_id, QUALITY_LABELS[quality_id], QUALITY_FORMATS[quality_id])
            )

    return VideoMetadata(
        url=normalized,
        title=info.get("title") or "downloaded-video",
        thumbnail=info.get("thumbnail"),
        duration=info.get("duration"),
        uploader=info.get("uploader") or info.get("channel") or info.get("creator"),
        source=info.get("extractor_key") or info.get("extractor"),
        qualities=qualities,
    )


def download_video(url: str, quality: str, output_path: Path) -> Path:
    import yt_dlp

    ffmpeg_error = check_ffmpeg()
    if ffmpeg_error:
        raise RuntimeError(ffmpeg_error)
    if quality not in QUALITY_FORMATS:
        raise RuntimeError("Chat luong tai ve khong hop le.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_template = str(output_path.parent / "_download_%(id)s.%(ext)s")
    errors: list[str] = []

    for index, format_selector in enumerate(QUALITY_FALLBACKS[quality]):
        _cleanup_download_temps(output_path.parent)
        opts: dict[str, Any] = {
            "format": format_selector,
            "outtmpl": temp_template,
            "continuedl": True,
            "retries": 5,
            "fragment_retries": 5,
            "concurrent_fragment_downloads": 4,
            "merge_output_format": "mp4",
            "noplaylist": True,
            "restrictfilenames": True,
            "windowsfilenames": True,
            "quiet": True,
            "no_warnings": True,
            **_cookie_options(),
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([normalize_video_url(url)])
            completed = _find_completed_file(output_path.parent)
            if completed is None:
                raise RuntimeError("Da tai xong nhung khong tim thay file video.")
            if output_path.exists():
                output_path.unlink()
            return completed.rename(output_path)
        except Exception as exc:
            errors.append(str(exc))
            if index == len(QUALITY_FALLBACKS[quality]) - 1:
                _cleanup_download_temps(output_path.parent)
                raise RuntimeError(friendly_yt_dlp_error("; ".join(errors))) from exc

    raise RuntimeError("Khong tai duoc video.")


def _find_completed_file(download_dir: Path) -> Path | None:
    candidates = [
        path
        for path in download_dir.glob("_download_*")
        if path.is_file()
        and not path.name.endswith((".part", ".ytdl", ".temp"))
        and ".part-" not in path.name
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _cleanup_download_temps(download_dir: Path) -> None:
    for path in download_dir.glob("_download_*"):
        if path.is_file():
            with suppress(OSError):
                path.unlink()
