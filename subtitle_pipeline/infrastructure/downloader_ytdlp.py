"""Tai video tu URL (YouTube/Douyin/TikTok... - moi trang yt-dlp ho tro) ve
thu muc job de xu ly nhu file upload binh thuong. Chay trong Celery worker
(stage "download", xem app/jobs/tasks.py) - KHONG tai trong process Streamlit
vi co the mat nhieu phut voi video dai.

Goi yt-dlp qua `sys.executable -m yt_dlp` (khong goi lenh `yt-dlp` truc tiep)
de chac chan dung ban trong venv dang chay worker - tranh loi PATH tren
Windows (cung ly do voi quy uoc `python -m celery` trong celery_app.py).
"""

import subprocess
import sys
from pathlib import Path

# Nhan chat luong (hien o UI) -> chuoi format cua yt-dlp. "720p" gioi han
# chieu cao de file nhe/nhanh (du cho pipeline 16kHz audio + xem lai); "best"
# lay ban tot nhat co san.
QUALITY_FORMATS = {
    "720p": "bv*[height<=720]+ba/b[height<=720]/b",
    "best": "bv*+ba/b",
}


def _build_download_command(url: str, out_dir: Path, quality: str) -> list[str]:
    if quality not in QUALITY_FORMATS:
        raise ValueError(f"Chất lượng tải chưa hỗ trợ: {quality}")
    return [
        sys.executable,
        "-m",
        "yt_dlp",
        "--no-playlist",
        # Ten file tu tieu de video nhung gioi han 80 ky tu + chi ASCII de
        # tranh loi duong dan Windows/ffmpeg voi unicode la.
        "--restrict-filenames",
        "-o",
        str(out_dir / "%(title).80s.%(ext)s"),
        "-f",
        QUALITY_FORMATS[quality],
        "--merge-output-format",
        "mp4",
        url,
    ]


def download_video(url: str, out_dir: Path, quality: str = "720p") -> Path:
    """Tai video ve `out_dir` va tra ve duong dan file. `out_dir` phai la thu
    muc job MOI (chi chua file tai ve) - ham tim file bang cach lay file moi
    nhat trong thu muc sau khi tai xong.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    before = set(out_dir.iterdir())
    cmd = _build_download_command(url, out_dir, quality)
    subprocess.run(cmd, check=True, capture_output=True, text=True)

    new_files = [p for p in out_dir.iterdir() if p.is_file() and p not in before]
    if not new_files:
        raise RuntimeError(f"yt-dlp chạy xong nhưng không thấy file tải về trong {out_dir}")
    return max(new_files, key=lambda p: p.stat().st_size)
