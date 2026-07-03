"""Dieu phoi long tieng (dubbing): synthesize giong doc tieu chuan (khong
clone giong goc - xem HANDOFF.md Phase 5b) cho tung segment DA DICH, dat
clip raw vao dung timeline, roi mux (ghep) vao video goc thay the audio cu.
Buoc nay chay SAU buoc dich
(application/translate.py), tach rieng vi la hanh dong tuy chon nguoi dung
kich hoat tu Editor (xem app/jobs/tasks.py: dub_job).

Sau khi mux xong, XOA toan bo `work_dir` (audio trung gian cua ca buoc
transcribe lan cac clip TTS/track am thanh tam) - chi giu lai file ket qua
trong `out_dir` (phu de + video da long tieng). Xem HANDOFF.md Phase 5b,
quyet dinh don file 2026-07-03.
"""

import shutil
import time
from pathlib import Path

from subtitle_pipeline.domain.models import SubtitleSegment
from subtitle_pipeline.infrastructure.audio_mux import build_dub_track, mux_audio_into_video
from subtitle_pipeline.infrastructure.audio_timing import probe_duration_seconds
from subtitle_pipeline.infrastructure.tts_edge import EdgeTTSSynthesizer

MAX_SYNTHESIZE_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 2.0


def _total_duration(work_dir: Path, source_video: Path) -> float:
    denoised_audio = work_dir / "audio_denoised.wav"
    if denoised_audio.exists():
        import soundfile as sf

        info = sf.info(str(denoised_audio))
        return info.frames / info.samplerate
    return probe_duration_seconds(source_video)


def _clean_text_for_speech(text: str) -> str:
    """`optimize_segments()` (application/optimize.py) chen `\\n` vao text de
    ngat dong HIEN THI tren phu de (vd. toi da 42 ky tu/dong) - dua thang
    chuoi co `\\n` do vao TTS lam giong doc bi ngat quang/loi giua chung. TTS
    chi can 1 cau lien tuc, khong lien quan gi toi cach ngat dong phu de.
    """
    return " ".join(text.split())


def _synthesize_with_retry(tts: EdgeTTSSynthesizer, text: str, output_path: Path) -> bool:
    """edge-tts thinh thoang loi mang/API thoang qua (xem HANDOFF.md Phase
    5b) - thu lai toi da MAX_SYNTHESIZE_ATTEMPTS lan truoc khi bo qua han
    segment nay (de lai khoang lang thay vi lam that bai ca job).
    """
    for attempt in range(1, MAX_SYNTHESIZE_ATTEMPTS + 1):
        try:
            tts.synthesize(text, output_path)
            return True
        except Exception as exc:
            if attempt == MAX_SYNTHESIZE_ATTEMPTS:
                print(f"[dub] Bo qua segment sau {attempt} lan loi: {exc}")
                return False
            time.sleep(RETRY_BACKOFF_SECONDS)
    return False


def dub_and_export(
    segments: list[SubtitleSegment],
    target_language: str,
    source_video: Path,
    work_dir: Path,
    out_dir: Path,
    stem: str,
    voice: str | None = None,
    keep_original_audio: bool = False,
) -> Path:
    segment_dir = work_dir / f"dub_{target_language}_segments"
    segment_dir.mkdir(parents=True, exist_ok=True)

    raw_clips: list[tuple[float, Path]] = []
    with EdgeTTSSynthesizer(target_language, voice=voice) as tts:
        for i, seg in enumerate(segments):
            text = _clean_text_for_speech(seg.text)
            if not text:
                continue

            raw_clip = segment_dir / f"{i:05d}_raw.wav"
            if not _synthesize_with_retry(tts, text, raw_clip):
                continue

            raw_clips.append((seg.start, raw_clip))
        sample_rate = tts.sample_rate

    total_duration = _total_duration(work_dir, source_video)
    dub_track_path = work_dir / f"dub_track_{target_language}.wav"
    build_dub_track(raw_clips, total_duration, sample_rate, dub_track_path)

    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"{stem}.{target_language}.dubbed.mp4"
    mux_audio_into_video(
        source_video, dub_track_path, output_path, keep_original_audio=keep_original_audio
    )

    shutil.rmtree(work_dir, ignore_errors=True)
    return output_path
