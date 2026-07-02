"""FFmpeg audio extraction - khong can model AI, chay CPU, khong can quan ly VRAM."""
import subprocess
from pathlib import Path


def extract_audio(input_path: Path, output_path: Path, sample_rate: int = 16000) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vn", "-ac", "1", "-ar", str(sample_rate),
        "-c:a", "pcm_s16le",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
