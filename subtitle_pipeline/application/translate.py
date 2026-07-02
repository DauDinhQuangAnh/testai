"""Dieu phoi dich + toi uu dong cho 1 danh sach segment - dung boi Celery task
translate_job (app/jobs/tasks.py). Tach rieng khoi TranscriptionPipeline vi day
la hanh dong tuy chon nguoi dung kich hoat sau khi job chinh da xong, khong
phai buoc bat buoc trong pipeline chinh.
"""
from pathlib import Path

from subtitle_pipeline.application.optimize import optimize_segments
from subtitle_pipeline.domain.models import SubtitleSegment
from subtitle_pipeline.export.formats import FORMAT_WRITERS
from subtitle_pipeline.infrastructure.translator_nllb import NLLBTranslator


def translate_and_export(
    segments: list[SubtitleSegment],
    source_language: str,
    target_language: str,
    device: str,
    out_dir: Path,
    stem: str,
) -> list[SubtitleSegment]:
    with NLLBTranslator(source_language, target_language, device) as translator:
        translated = translator.translate(segments)
    optimized = optimize_segments(translated)

    out_dir.mkdir(parents=True, exist_ok=True)
    for fmt, writer in FORMAT_WRITERS.items():
        (out_dir / f"{stem}.{target_language}.{fmt}").write_text(
            writer(optimized), encoding="utf-8"
        )
    return optimized
