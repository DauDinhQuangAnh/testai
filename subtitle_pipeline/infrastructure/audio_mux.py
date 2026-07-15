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
        # Cong don thay vi gan de (=) - neu 2 clip chong lan (cau TTS dai hon
        # khoang trong, da tang toc het nguong ma van tran - xem
        # application/dub.py), ca 2 cung nghe duoc thay vi clip sau cat cut
        # clip truoc roi de sot duoi clip truoc phat lai sau do.
        track[start_sample:end_sample] += data[: end_sample - start_sample]

    np.clip(track, -1.0, 1.0, out=track)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), track, sample_rate)


# Muc giam am luong tieng goc mac dinh khi giu tieng: 0.3 = giam 70% (kieu
# thuyet minh/voice-over phim tai lieu - giu khong khi nen, de tieng dich len).
KEEP_ORIGINAL_VOLUME = 0.3


def _build_mux_command(
    video_path: Path,
    audio_path: Path,
    output_path: Path,
    original_volume: float,
    dub_volume: float = 1.0,
    ducking: bool = False,
) -> list[str]:
    """Ham thuan dung lenh ffmpeg (tach rieng de test khong can ffmpeg that).

    - original_volume=0: thay audio hoan toan bang track long tieng (che do
      "xoa tieng goc" cu - gio la 1 diem tren slider thay vi radio rieng).
    - original_volume>0: tron tieng goc (giam con muc nay) voi track long
      tieng - `amix normalize=0` de amix khong tu chia deu am luong 2 track.
      LUU Y: yeu cau video goc PHAI co audio stream (`0:a:0`).
    - dub_volume: he so am luong track long tieng (1.0 = giu nguyen).
    - ducking: tu dong nen tieng goc XUONG THEM moi khi giong long tieng dang
      noi (ffmpeg sidechaincompress, track dub lam sidechain) - tieng goc chi
      to len o khoang lang giua cac cau, kieu thuyet minh chuyen nghiep.
      Can `asplit` vi track dub dung 2 lan (lam sidechain + tron vao output).
    """
    base = ["ffmpeg", "-y", "-i", str(video_path), "-i", str(audio_path)]
    if original_volume <= 0:
        if dub_volume == 1.0:
            audio_args = ["-map", "0:v:0", "-map", "1:a:0"]
        else:
            audio_args = [
                "-filter_complex",
                f"[1:a:0]volume={dub_volume}[aout]",
                "-map",
                "0:v:0",
                "-map",
                "[aout]",
            ]
    elif ducking:
        filter_complex = (
            f"[1:a:0]volume={dub_volume},asplit=2[sc][dub];"
            f"[0:a:0]volume={original_volume}[bg];"
            f"[bg][sc]sidechaincompress=threshold=0.02:ratio=12:attack=50:release=400[duck];"
            f"[duck][dub]amix=inputs=2:duration=longest:normalize=0[aout]"
        )
        audio_args = ["-filter_complex", filter_complex, "-map", "0:v:0", "-map", "[aout]"]
    else:
        filter_complex = (
            f"[1:a:0]volume={dub_volume}[dub];"
            f"[0:a:0]volume={original_volume}[bg];"
            f"[bg][dub]amix=inputs=2:duration=longest:normalize=0[aout]"
        )
        audio_args = ["-filter_complex", filter_complex, "-map", "0:v:0", "-map", "[aout]"]
    return [*base, *audio_args, "-c:v", "copy", "-c:a", "aac", "-shortest", str(output_path)]


def mux_audio_into_video(
    video_path: Path,
    audio_path: Path,
    output_path: Path,
    original_volume: float = 0.0,
    dub_volume: float = 1.0,
    ducking: bool = False,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = _build_mux_command(
        video_path, audio_path, output_path, original_volume, dub_volume, ducking
    )
    subprocess.run(cmd, check=True, capture_output=True, text=True)


# Preset chat luong render (chi dung khi phai re-encode video, tuc hardsub -
# khong hardsub thi video stream duoc copy nguyen ven, nhanh hon nhieu).
QUALITY_CRF = {"fast": 28, "balanced": 23, "high": 18}


def _build_burn_command(video_path: Path, ass_filename: str, output_path: Path, crf: int):
    # Chi truyen TEN file .ass (khong phai duong dan day du) - lenh nay phai
    # chay voi cwd = thu muc chua file .ass, vi filter `ass=` cua ffmpeg parse
    # dau `:` va `\` trong duong dan Windows rat loi (C:\... bi hieu nham la
    # tham so filter). Xem burn_subtitles().
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        f"ass={ass_filename}",
        "-c:v",
        "libx264",
        "-crf",
        str(crf),
        "-c:a",
        "copy",
        str(output_path),
    ]


def burn_subtitles(
    video_path: Path, ass_path: Path, output_path: Path, quality: str = "balanced"
) -> None:
    """Gan cung (hardsub) phu de .ass vao video - re-encode video stream bang
    libx264 voi CRF theo preset `quality` (xem QUALITY_CRF), audio copy
    nguyen ven. Cham hon mux thuong dang ke (phai encode lai toan bo hinh).
    """
    crf = QUALITY_CRF.get(quality, QUALITY_CRF["balanced"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = _build_burn_command(video_path.resolve(), ass_path.name, output_path.resolve(), crf)
    subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=str(ass_path.parent))
