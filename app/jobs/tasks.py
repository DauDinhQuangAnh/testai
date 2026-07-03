"""Celery task chay AI pipeline (Phase 2 - subtitle_pipeline) cho 1 Job va cap
nhat trang thai/tien do vao DB de Streamlit Dashboard hien thi.
"""

import json
from pathlib import Path

from app.db.models import Job, JobStatus
from app.jobs.celery_app import celery_app
from app.jobs.repository import JobRepository
from subtitle_pipeline.application.dub import dub_and_export
from subtitle_pipeline.application.pipeline import TranscriptionPipeline
from subtitle_pipeline.application.translate import translate_and_export
from subtitle_pipeline.config import PipelineConfig
from subtitle_pipeline.domain.models import SubtitleSegment
from subtitle_pipeline.export.formats import FORMAT_WRITERS


@celery_app.task(name="app.jobs.tasks.process_video_job")
def process_video_job(
    job_id: str, target_language: str | None = None, voice: str | None = None
) -> None:
    """Chay pipeline chinh (transcribe). Neu co `target_language`, chay tiep
    LUON trong cung 1 job: dich -> long tieng -> mux video - nguoi dung chi
    can upload 1 lan va chon ngon ngu, khong can vao Editor bam gi them (xem
    HANDOFF.md Phase 5b, quyet dinh gop flow 2026-07-03). `job.stage` duoc cap
    nhat xuyen suot ca 2 giai doan de Dashboard hien tien do dung.
    `voice`: ten giong Edge TTS (xem tts_edge.VOICE_OPTIONS), None = giong
    mac dinh cua ngon ngu.
    """
    repo = JobRepository()
    job = repo.get(job_id)
    if job is None:
        return

    repo.update_status(job_id, status=JobStatus.RUNNING, stage="starting")

    def on_stage(name: str) -> None:
        repo.update_status(job_id, status=JobStatus.RUNNING, stage=name)

    try:
        config = PipelineConfig.from_env()
        work_dir = Path(job.output_dir) / "_work"
        pipeline = TranscriptionPipeline(config=config, work_dir=work_dir)
        segments, detected_language = pipeline.run(Path(job.input_path), on_stage=on_stage)

        out_dir = Path(job.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(job.input_path).stem
        for fmt, writer in FORMAT_WRITERS.items():
            (out_dir / f"{stem}.{fmt}").write_text(writer(segments), encoding="utf-8")
        # Luu lai ngon ngu THAT cua audio (Whisper auto-detect, xem
        # pipeline.py) de translate_job/dub_job (chay Celery task rieng, chi
        # co file tren dia, khong co bien nay trong bo nho) doc lai dung -
        # xem _read_source_language() ben duoi.
        (out_dir / f"{stem}.source_language.txt").write_text(detected_language, encoding="utf-8")

        if target_language:
            try:
                on_stage("translate")
                translated = translate_and_export(
                    segments, detected_language, target_language, config.device, out_dir, stem
                )

                on_stage("dub")
                dub_and_export(
                    segments=translated,
                    target_language=target_language,
                    source_video=Path(job.input_path),
                    work_dir=work_dir,
                    out_dir=out_dir,
                    stem=stem,
                    voice=voice,
                )
            except Exception as exc:
                # KHONG lam FAILED ca job - transcribe da thanh cong, phu de
                # goc van dung duoc (vd. ngon ngu nguon hiem NLLB chua ho
                # tro). Ghi ro ly do vao error_message de Dashboard hien
                # canh bao, nhung job van DONE.
                repo.update_status(
                    job_id,
                    status=JobStatus.RUNNING,
                    stage="translate_dub_skipped",
                    error_message=f"Bo qua dich/long tieng: {exc}",
                )

        repo.update_status(job_id, status=JobStatus.DONE, stage="done")
    except Exception as exc:
        repo.update_status(job_id, status=JobStatus.FAILED, stage=None, error_message=str(exc))
        raise


def _read_source_language(out_dir: Path, stem: str, config: PipelineConfig) -> str:
    """Doc ngon ngu nguon THAT (Whisper auto-detect, ghi boi process_video_job
    vao `{stem}.source_language.txt`). Fallback ve `config.language` (mac
    dinh tinh tu .env) cho job cu tao truoc khi co file sidecar nay.
    """
    sidecar = out_dir / f"{stem}.source_language.txt"
    if sidecar.exists():
        return sidecar.read_text(encoding="utf-8").strip()
    return config.language


@celery_app.task(name="app.jobs.tasks.translate_job")
def translate_job(job_id: str, target_language: str) -> None:
    repo = JobRepository()
    job = repo.get(job_id)
    if job is None:
        return

    out_dir = Path(job.output_dir)
    stem = Path(job.input_path).stem
    json_path = out_dir / f"{stem}.json"
    if not json_path.exists():
        return

    with open(json_path, encoding="utf-8") as f:
        segments = [SubtitleSegment(**seg) for seg in json.load(f)]

    config = PipelineConfig.from_env()
    source_language = _read_source_language(out_dir, stem, config)
    translate_and_export(segments, source_language, target_language, config.device, out_dir, stem)


def _load_or_translate_segments(
    job: Job, target_language: str, config: PipelineConfig
) -> list[SubtitleSegment]:
    """Doc segment da dich (`{stem}.{lang}.json`) neu da co san (vd. nguoi dung
    tung bam "Dich" rieng truoc do), neu chua co thi tu dich tu segment goc
    (`{stem}.json`) - dung boi dub_job de nguoi dung chi can bam 1 nut "Dich +
    Long tieng" duy nhat (xem HANDOFF.md Phase 5b), khong bat buoc phai dich
    truoc.
    """
    out_dir = Path(job.output_dir)
    stem = Path(job.input_path).stem

    translated_json_path = out_dir / f"{stem}.{target_language}.json"
    if translated_json_path.exists():
        with open(translated_json_path, encoding="utf-8") as f:
            return [SubtitleSegment(**seg) for seg in json.load(f)]

    with open(out_dir / f"{stem}.json", encoding="utf-8") as f:
        original_segments = [SubtitleSegment(**seg) for seg in json.load(f)]
    source_language = _read_source_language(out_dir, stem, config)
    return translate_and_export(
        original_segments, source_language, target_language, config.device, out_dir, stem
    )


@celery_app.task(name="app.jobs.tasks.dub_job")
def dub_job(job_id: str, target_language: str, voice: str | None = None) -> None:
    repo = JobRepository()
    job = repo.get(job_id)
    if job is None:
        return

    out_dir = Path(job.output_dir)
    stem = Path(job.input_path).stem
    if not (out_dir / f"{stem}.json").exists():
        return

    config = PipelineConfig.from_env()
    segments = _load_or_translate_segments(job, target_language, config)

    work_dir = out_dir / "_work"
    dub_and_export(
        segments=segments,
        target_language=target_language,
        source_video=Path(job.input_path),
        work_dir=work_dir,
        out_dir=out_dir,
        stem=stem,
        voice=voice,
    )
