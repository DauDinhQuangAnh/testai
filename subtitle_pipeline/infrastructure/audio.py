"""FFmpeg audio extraction - khong can model AI, chay CPU, khong can quan ly VRAM."""

import subprocess
from pathlib import Path


def extract_audio(input_path: Path, output_path: Path, sample_rate: int = 16000) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def _build_trim_command(input_path: Path, output_path: Path, seconds: float) -> list[str]:
    # -c copy: cat nhanh khong re-encode. Diem cat co the lech nhe theo
    # keyframe - chap nhan duoc cho muc dich "chay thu doan ngan".
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-t",
        str(seconds),
        "-c",
        "copy",
        str(output_path),
    ]


def trim_media(input_path: Path, output_path: Path, seconds: float) -> None:
    """Cat `seconds` giay dau cua video/audio - dung cho che do "kiem thu"
    (chay thu doan ngan de xem truoc giong/dich truoc khi chay ca video dai,
    xem app/jobs/tasks.py).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = _build_trim_command(input_path, output_path, seconds)
    subprocess.run(cmd, check=True, capture_output=True, text=True)
