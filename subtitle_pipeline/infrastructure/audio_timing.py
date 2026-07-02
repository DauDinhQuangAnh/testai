"""FFmpeg/ffprobe helper de do do dai va co-gian (time-stretch, giu nguyen cao
do) 1 file audio khop voi 1 khoang thoi gian muc tieu - dung boi
application/dub.py de can chinh do dai cau TTS sinh ra khop voi khung thoi
gian [start, end] cua segment phu de goc. Khong can model AI, chi goi
subprocess ffmpeg/ffprobe (cung style voi infrastructure/audio.py).
"""

import subprocess
from pathlib import Path


def probe_duration_seconds(path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return float(result.stdout.strip())


def _clamp_atempo_factors(factor: float) -> list[float]:
    """Ffmpeg atempo chi nhan gia tri trong [0.5, 2.0] moi lan goi - tach 1
    factor bat ky (>0) thanh chuoi factor con trong khoang do, nhan lai voi
    nhau bang dung factor goc. Ham thuan, khong goi ffmpeg - test duoc rieng
    (xem tests/test_audio_timing.py).
    """
    if factor <= 0:
        raise ValueError("factor phai > 0")
    factors: list[float] = []
    remaining = factor
    while remaining > 2.0:
        factors.append(2.0)
        remaining /= 2.0
    while remaining < 0.5:
        factors.append(0.5)
        remaining /= 0.5
    factors.append(remaining)
    return factors


def time_stretch_to_duration(input_path: Path, output_path: Path, target_duration: float) -> None:
    if target_duration <= 0:
        raise ValueError("target_duration phai > 0")
    current_duration = probe_duration_seconds(input_path)
    factor = current_duration / target_duration
    atempo_chain = ",".join(f"atempo={f:.6f}" for f in _clamp_atempo_factors(factor))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-i", str(input_path), "-filter:a", atempo_chain, str(output_path)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
