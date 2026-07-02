"""Dung 1 track audio day du theo timeline goc tu cac doan TTS raw, roi mux
(ghep) track do vao video goc thay the audio cu - buoc cuoi cua flow long
tieng (application/dub.py).

`build_dub_track` dung numpy de dat tung clip vao dung vi tri offset trong 1
mang zero (khoang lang giua cac cau se la im lang, giong video goc khong co
loi noi lien tuc). numpy da co san qua torch (dependency cua cac adapter
khac), soundfile can khai bao trong requirements.txt.
"""

import subprocess
from pathlib import Path


def _resample_linear(data, src_rate: int, dst_rate: int):
    import numpy as np

    if src_rate == dst_rate or len(data) == 0:
        return data
    duration = len(data) / src_rate
    dst_length = max(1, int(round(duration * dst_rate)))
    src_indices = np.linspace(0, len(data) - 1, num=dst_length)
    return np.interp(src_indices, np.arange(len(data)), data).astype(data.dtype)


def build_dub_track(
    clips: list[tuple[float, Path]], total_duration: float, sample_rate: int, output_path: Path
) -> None:
    import numpy as np
    import soundfile as sf

    total_samples = max(1, int(round(total_duration * sample_rate)))
    track = np.zeros(total_samples, dtype=np.float32)

    for start_seconds, clip_path in clips:
        data, clip_rate = sf.read(str(clip_path), dtype="float32")
        if data.ndim > 1:
            data = data.mean(axis=1)
        data = _resample_linear(data, clip_rate, sample_rate)

        start_sample = int(round(start_seconds * sample_rate))
        if start_sample >= total_samples:
            continue
        end_sample = min(start_sample + len(data), total_samples)
        track[start_sample:end_sample] = data[: end_sample - start_sample]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), track, sample_rate)


def mux_audio_into_video(video_path: Path, audio_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(audio_path),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
