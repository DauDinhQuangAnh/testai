"""Dieu phoi long tieng (dubbing): synthesize giong doc tieu chuan (khong
clone giong goc - xem HANDOFF.md Phase 5b) cho tung segment DA DICH, co-gian
khop khung thoi gian goc, dung thanh 1 track audio day du theo timeline, roi
mux (ghep) vao video goc thay the audio cu. Buoc nay chay SAU buoc dich
(application/translate.py), tach rieng vi la hanh dong tuy chon nguoi dung
kich hoat tu Editor (xem app/jobs/tasks.py: dub_job).
"""
from pathlib import Path

from subtitle_pipeline.domain.models import SubtitleSegment
from subtitle_pipeline.infrastructure.audio_mux import build_dub_track, mux_audio_into_video
from subtitle_pipeline.infrastructure.audio_timing import (
    probe_duration_seconds,
    time_stretch_to_duration,
)
from subtitle_pipeline.infrastructure.tts_mms import MMSTTSSynthesizer

MIN_SEGMENT_DURATION_SECONDS = 0.05


def _total_duration(work_dir: Path, source_video: Path) -> float:
    denoised_audio = work_dir / "audio_denoised.wav"
    if denoised_audio.exists():
        import soundfile as sf

        info = sf.info(str(denoised_audio))
        return info.frames / info.samplerate
    return probe_duration_seconds(source_video)


def dub_and_export(
    segments: list[SubtitleSegment],
    target_language: str,
    device: str,
    source_video: Path,
    work_dir: Path,
    out_dir: Path,
    stem: str,
) -> Path:
    segment_dir = work_dir / f"dub_{target_language}_segments"
    segment_dir.mkdir(parents=True, exist_ok=True)

    stretched_clips: list[tuple[float, Path]] = []
    with MMSTTSSynthesizer(target_language, device) as tts:
        for i, seg in enumerate(segments):
            raw_clip = segment_dir / f"{i:05d}_raw.wav"
            tts.synthesize(seg.text, raw_clip)

            duration = max(seg.end - seg.start, MIN_SEGMENT_DURATION_SECONDS)
            stretched_clip = segment_dir / f"{i:05d}_stretched.wav"
            time_stretch_to_duration(raw_clip, stretched_clip, duration)
            stretched_clips.append((seg.start, stretched_clip))
        sample_rate = tts.sample_rate

    total_duration = _total_duration(work_dir, source_video)
    dub_track_path = work_dir / f"dub_track_{target_language}.wav"
    build_dub_track(stretched_clips, total_duration, sample_rate, dub_track_path)

    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"{stem}.{target_language}.dubbed.mp4"
    mux_audio_into_video(source_video, dub_track_path, output_path)
    return output_path
