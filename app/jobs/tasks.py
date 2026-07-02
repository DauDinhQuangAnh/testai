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
def process_video_job(job_id: str, target_language: str | None = None) -> None:
    """Chay pipeline chinh (transcribe). Neu co `target_language`, chay tiep
    LUON trong cung 1 job: dich -> long tieng -> mux video - nguoi dung chi
    can upload 1 lan va chon ngon ngu, khong can vao Editor bam gi them (xem
    HANDOFF.md Phase 5b, quyet dinh gop flow 2026-07-03). `job.stage` duoc cap
    nhat xuyen suot ca 2 giai doan de Dashboard hien tien do dung.
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
        segments = pipeline.run(Path(job.input_path), on_stage=on_stage)

        out_dir = Path(job.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(job.input_path).stem
        for fmt, writer in FORMAT_WRITERS.items():
            (out_dir / f"{stem}.{fmt}").write_text(writer(segments), encoding="utf-8")

        if target_language:
            on_stage("translate")
            translated = translate_and_export(
                segments, config.language, target_language, config.device, out_dir, stem
            )

            on_stage("dub")
            dub_and_export(
                segments=translated,
                target_language=target_language,
                device=config.device,
                source_video=Path(job.input_path),
                work_dir=work_dir,
                out_dir=out_dir,
                stem=stem,
            )

        repo.update_status(job_id, status=JobStatus.DONE, stage="done")
    except Exception as exc:
        repo.update_status(job_id, status=JobStatus.FAILED, stage=None, error_message=str(exc))
        raise


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
    translate_and_export(segments, config.language, target_language, config.device, out_dir, stem)


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
    return translate_and_export(
        original_segments, config.language, target_language, config.device, out_dir, stem
    )


@celery_app.task(name="app.jobs.tasks.dub_job")
def dub_job(job_id: str, target_language: str) -> None:
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
        device=config.device,
        source_video=Path(job.input_path),
        work_dir=work_dir,
        out_dir=out_dir,
        stem=stem,
    )
