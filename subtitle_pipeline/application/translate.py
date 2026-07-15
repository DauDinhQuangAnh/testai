"""Dieu phoi dich + toi uu dong cho 1 danh sach segment - dung boi Celery task
translate_job (app/jobs/tasks.py). Tach rieng khoi TranscriptionPipeline vi day
la hanh dong tuy chon nguoi dung kich hoat sau khi job chinh da xong, khong
phai buoc bat buoc trong pipeline chinh.

Engine dich chon tu dong theo cau hinh: co GEMINI_API_KEY -> Gemini (LLM,
dich theo ngu canh, xem translator_gemini.py), khong co -> NLLB local nhu
truoc. Gemini loi giua chung (mat mang/het quota) thi fallback ve NLLB ngay
trong cung lan dich - khong lam fail job, chi mat chat luong ngu canh.
"""

import os
from dataclasses import replace
from pathlib import Path

from subtitle_pipeline.application.glossary import mask_terms, parse_glossary, restore_terms
from subtitle_pipeline.application.optimize import (
    DEFAULT_MAX_CHARS_PER_LINE,
    DEFAULT_MAX_LINES,
    optimize_segments,
)
from subtitle_pipeline.application.sentence_merge import merge_into_sentences
from subtitle_pipeline.domain.models import SubtitleSegment
from subtitle_pipeline.export.formats import FORMAT_WRITERS
from subtitle_pipeline.infrastructure.translator_gemini import GeminiTranslator
from subtitle_pipeline.infrastructure.translator_nllb import NLLBTranslator


def _translate_segments(
    sentences: list[SubtitleSegment], source_language: str, target_language: str, device: str
) -> list[SubtitleSegment]:
    """Dich bang Gemini neu co GEMINI_API_KEY, fallback NLLB local khi khong
    co key hoac Gemini loi (da tu retry ben trong GeminiTranslator roi).
    """
    if os.environ.get("GEMINI_API_KEY"):
        try:
            with GeminiTranslator(source_language, target_language) as translator:
                return translator.translate(sentences)
        except Exception as exc:
            print(f"[translate] Gemini lỗi ({exc}) - chuyển sang NLLB chạy máy")
    with NLLBTranslator(source_language, target_language, device) as translator:
        return translator.translate(sentences)


def translate_and_export(
    segments: list[SubtitleSegment],
    source_language: str,
    target_language: str,
    device: str,
    out_dir: Path,
    stem: str,
    glossary_text: str = "",
    max_chars_per_line: int = DEFAULT_MAX_CHARS_PER_LINE,
    max_lines: int = DEFAULT_MAX_LINES,
) -> list[SubtitleSegment]:
    # Gop manh cau (WhisperX hay chia o muc tu/cum tu) thanh cau hoan chinh
    # TRUOC khi dich - NLLB co du ngu canh nen dich tu nhien hon han so voi
    # dich tung manh roi rac (xem HANDOFF.md). CHI ap dung cho nhanh dich,
    # khong dung toi phu de goc chua dich.
    sentences = merge_into_sentences(segments)

    # Bang thuat ngu: mask term nguon truoc khi dich, restore term dich sau -
    # cach duy nhat ep NLLB giu dung thuat ngu (xem glossary.py).
    glossary = parse_glossary(glossary_text)
    if glossary:
        sentences = [replace(seg, text=mask_terms(seg.text, glossary)) for seg in sentences]

    translated = _translate_segments(sentences, source_language, target_language, device)

    if glossary:
        translated = [replace(seg, text=restore_terms(seg.text, glossary)) for seg in translated]

    optimized = optimize_segments(
        translated, max_chars_per_line=max_chars_per_line, max_lines=max_lines
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    for fmt, writer in FORMAT_WRITERS.items():
        (out_dir / f"{stem}.{target_language}.{fmt}").write_text(
            writer(optimized), encoding="utf-8"
        )
    return optimized
