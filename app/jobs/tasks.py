"""Celery task chay AI pipeline (Phase 2 - subtitle_pipeline) cho 1 Job va cap
nhat trang thai/tien do vao DB de Streamlit Dashboard hien thi.
"""
import json
from pathlib import Path

from app.db.models import JobStatus
from app.jobs.celery_app import celery_app
from app.jobs.repository import JobRepository
from subtitle_pipeline.application.pipeline import TranscriptionPipeline
from subtitle_pipeline.application.translate import translate_and_export
from subtitle_pipeline.config import PipelineConfig
from subtitle_pipeline.domain.models import SubtitleSegment
from subtitle_pipeline.export.formats import FORMAT_WRITERS


@celery_app.task(name="app.jobs.tasks.process_video_job")
def process_video_job(job_id: str) -> None:
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
