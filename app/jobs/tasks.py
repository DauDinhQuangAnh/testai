"""Celery task chay AI pipeline (Phase 2 - subtitle_pipeline) cho 1 Job va cap
nhat trang thai/tien do vao DB de FE React (frontend/) poll qua backend API
hien thi.

`process_video_job` nhan 1 dict `options` (toan bo lua chon tu wizard 6 buoc
o frontend/src/pages/NewJob.tsx - xem type JobOptions trong
frontend/src/lib/types.ts, luu song song vao
`job_config.json` trong thu muc job de trace/tao lai). Cac task
translate_job/dub_job (Editor) van giu tham so roi don gian.
"""

import json
from pathlib import Path

from app.db.models import Job, JobStatus
from app.jobs.celery_app import celery_app
from app.jobs.repository import JobRepository
from subtitle_pipeline.application.dub import DubRenderOptions, dub_and_export
from subtitle_pipeline.application.pipeline import TranscriptionPipeline
from subtitle_pipeline.application.pronunciation import resolve_pronunciation_glossary
from subtitle_pipeline.application.translate import translate_and_export
from subtitle_pipeline.config import PipelineConfig
from subtitle_pipeline.domain.models import SubtitleSegment
from subtitle_pipeline.export.formats import FORMAT_WRITERS, SubtitleStyle
from subtitle_pipeline.infrastructure.audio import trim_media
from subtitle_pipeline.infrastructure.downloader_ytdlp import download_video
from subtitle_pipeline.infrastructure.transcriber_faster_whisper import FasterWhisperTranscriber


def _build_dub_options(options: dict) -> DubRenderOptions:
    dubbing = options.get("dubbing") or {}
    audio = options.get("audio") or {}
    subtitle = options.get("subtitle") or {}
    output = options.get("output") or {}
    translation = options.get("translation") or {}
    target_language = dubbing.get("target_language", "vi")
    return DubRenderOptions(
        voice=dubbing.get("voice"),
        rate_percent=int(dubbing.get("rate_percent", 0)),
        pitch_hz=int(dubbing.get("pitch_hz", 0)),
        original_volume=float(audio.get("original_volume", 0.0)),
        dub_volume=float(audio.get("dub_volume", 1.0)),
        ducking=bool(audio.get("ducking", False)),
        output_format=output.get("format", "mp4"),
        burn_subtitles=bool(subtitle.get("burn_in", False)),
        subtitle_style=SubtitleStyle(**(subtitle.get("style") or {})),
        render_quality=output.get("quality", "balanced"),
        pronunciation=resolve_pronunciation_glossary(
            target_language, translation.get("pronunciation", "")
        ),
    )


def _resolve_input(job: Job, source: dict) -> Path:
    """Chuan bi file input: cat ngan neu bat che do kiem thu doan ngan."""
    job_dir = Path(job.output_dir).parent
    input_path = Path(job.input_path)

    download = source.get("download") or {}
    if source.get("input_mode") == "download" and download.get("url"):
        download_video(download["url"], download.get("quality", "best"), input_path)

    trim_seconds = source.get("trim_seconds")
    if trim_seconds:
        trimmed = job_dir / f"_trimmed_{trim_seconds}s{input_path.suffix}"
        trim_media(input_path, trimmed, trim_seconds)
        return trimmed
    return input_path


def _cleanup_downloaded_input(job: Job) -> None:
    job_dir = Path(job.output_dir).parent
    input_path = Path(job.input_path)
    for path in [input_path, *job_dir.glob("_trimmed_*")]:
        if path.is_file():
            try:
                path.unlink()
            except OSError:
                pass


@celery_app.task(name="app.jobs.tasks.process_video_job")
def process_video_job(job_id: str, options: dict | None = None) -> None:
    """Chay het flow trong 1 job: transcribe -> (dich -> long tieng -> render
    neu bat) theo `options` tu wizard Upload. `job.stage` cap nhat xuyen suot
    de Dashboard hien tien do.
    """
    options = options or {}
    repo = JobRepository()
    job = repo.get(job_id)
    if job is None:
        return

    repo.update_status(job_id, status=JobStatus.RUNNING, stage="starting")

    def on_stage(name: str) -> None:
        repo.update_status(job_id, status=JobStatus.RUNNING, stage=name)

    try:
        config = PipelineConfig.from_env()
        source = options.get("source") or {}
        downloaded_source = source.get("input_mode") == "download"
        if downloaded_source:
            on_stage("download")
        input_path = _resolve_input(job, source)

        # Ep cung ngon ngu nguon neu nguoi dung chon (mac dinh auto-detect).
        transcriber_factory = None
        forced_language = source.get("source_language")
        if forced_language:
            transcriber_factory = lambda: FasterWhisperTranscriber(  # noqa: E731
                config.whisper_model,
                config.whisper_compute_type,
                config.device,
                language=forced_language,
            )

        work_dir = Path(job.output_dir) / "_work"
        pipeline = TranscriptionPipeline(
            config=config, work_dir=work_dir, transcriber_factory=transcriber_factory
        )
        segments, detected_language = pipeline.run(input_path, on_stage=on_stage)

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

        dubbing = options.get("dubbing") or {}
        if dubbing.get("enabled") and dubbing.get("target_language"):
            translation = options.get("translation") or {}
            try:
                on_stage("translate")
                translated = translate_and_export(
                    segments,
                    detected_language,
                    dubbing["target_language"],
                    config.device,
                    out_dir,
                    stem,
                    glossary_text=translation.get("glossary", ""),
                    max_chars_per_line=int(translation.get("max_chars_per_line", 42)),
                    max_lines=int(translation.get("max_lines", 2)),
                )

                on_stage("dub")
                dub_and_export(
                    segments=translated,
                    target_language=dubbing["target_language"],
                    source_video=input_path,
                    work_dir=work_dir,
                    out_dir=out_dir,
                    stem=stem,
                    options=_build_dub_options(options),
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
                    error_message=f"Bỏ qua dịch/lồng tiếng: {exc}",
                )

        repo.update_status(job_id, status=JobStatus.DONE, stage="done")
    except Exception as exc:
        repo.update_status(job_id, status=JobStatus.FAILED, stage=None, error_message=str(exc))
        raise
    finally:
        source = options.get("source") or {}
        if source.get("input_mode") == "download":
            _cleanup_downloaded_input(job)


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
def dub_job(
    job_id: str,
    target_language: str,
    voice: str | None = None,
    keep_original_audio: bool = False,
) -> None:
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
        # Editor chi co 2 lua chon don gian (giong + giu/xoa tieng goc) -
        # muon tinh chinh sau (ducking, hardsub, toc do...) thi tao job moi
        # tu wizard Upload voi day du buoc.
        options=DubRenderOptions(
            voice=voice,
            original_volume=0.3 if keep_original_audio else 0.0,
            pronunciation=resolve_pronunciation_glossary(target_language),
        ),
    )
