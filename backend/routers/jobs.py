"""CRUD job + file ket qua. Logic tao job/tao lai/nhom file port 1:1 tu
wizard Streamlit cu (app/pages/1_Upload.py, 2_Dashboard.py) - options dict
giu NGUYEN schema nen Celery worker khong doi gi.
"""

import json
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.config import AppConfig
from app.db.models import Job
from app.jobs.tasks import process_video_job
from backend.db import job_repo
from backend.schemas import (
    FileOut,
    JobFilesOut,
    JobOut,
    SubtitleGroupOut,
    VideoOut,
)
from backend.security import AuthUser, get_current_user

router = APIRouter(prefix="/jobs", tags=["jobs"])

ALLOWED_EXTENSIONS = {"mp4", "mkv", "mov", "wav", "mp3", "m4a"}
MAX_FILE_SIZE_MB = 500
_INTERNAL_SUFFIXES = (".source_language.txt",)
_VIDEO_SUFFIXES = {".mp4", ".mkv", ".mov", ".webm"}


def _get_owned_job(job_id: str, user: AuthUser) -> Job:
    job = job_repo().get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy job")
    if not user.is_admin and job.user_id != user.id:
        # Tra 404 (khong phai 403) de khong lo thong tin job ton tai.
        raise HTTPException(status_code=404, detail="Không tìm thấy job")
    return job


def _create_job_from_options(
    options: dict, user: AuthUser, upload: UploadFile | None = None
) -> Job:
    job_id = str(uuid.uuid4())
    job_dir = AppConfig.from_env().storage_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    if upload is not None and upload.filename:
        extension = upload.filename.rsplit(".", 1)[-1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Định dạng '.{extension}' không hỗ trợ")
        data = upload.file.read()
        if len(data) > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"File quá {MAX_FILE_SIZE_MB}MB")
        filename = upload.filename
        input_path = job_dir / filename
        input_path.write_bytes(data)
    else:
        raise HTTPException(status_code=400, detail="Cần file upload")

    (job_dir / "job_config.json").write_text(
        json.dumps(options, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    job = job_repo().create(
        filename=filename,
        input_path=input_path,
        output_dir=job_dir / "output",
        job_id=job_id,
        user_id=None if user.is_admin else user.id,
    )
    process_video_job.delay(job.id, options)
    return job


@router.post("", response_model=JobOut)
def create_job(
    options: str = Form(...),
    file: UploadFile | None = File(default=None),
    user: AuthUser = Depends(get_current_user),
) -> JobOut:
    try:
        parsed = json.loads(options)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"options không phải JSON: {exc}") from exc
    return JobOut.from_job(_create_job_from_options(parsed, user, file))


@router.get("", response_model=list[JobOut])
def list_jobs(user: AuthUser = Depends(get_current_user)) -> list[JobOut]:
    repo = job_repo()
    jobs = repo.list_all() if user.is_admin else repo.list_by_user(user.id)
    return [JobOut.from_job(j) for j in jobs]


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, user: AuthUser = Depends(get_current_user)) -> JobOut:
    return JobOut.from_job(_get_owned_job(job_id, user))


@router.delete("/{job_id}")
def delete_job(job_id: str, user: AuthUser = Depends(get_current_user)) -> dict:
    job = _get_owned_job(job_id, user)
    shutil.rmtree(Path(job.output_dir).parent, ignore_errors=True)
    job_repo().delete(job.id)
    return {"deleted": job_id}


@router.post("/{job_id}/rerun", response_model=JobOut)
def rerun_job(job_id: str, user: AuthUser = Depends(get_current_user)) -> JobOut:
    job = _get_owned_job(job_id, user)
    config_path = Path(job.output_dir).parent / "job_config.json"
    if not config_path.exists():
        raise HTTPException(status_code=400, detail="Job này không có job_config.json để tạo lại")
    options = json.loads(config_path.read_text(encoding="utf-8"))

    new_id = str(uuid.uuid4())
    new_dir = AppConfig.from_env().storage_dir / new_id
    new_dir.mkdir(parents=True, exist_ok=True)

    source_file = Path(job.input_path)
    if not source_file.exists():
        raise HTTPException(status_code=400, detail="File gốc không còn trên đĩa")
    filename = source_file.name
    input_path = new_dir / filename
    shutil.copy2(source_file, input_path)

    (new_dir / "job_config.json").write_text(
        json.dumps(options, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    new_job = job_repo().create(
        filename=filename,
        input_path=input_path,
        output_dir=new_dir / "output",
        job_id=new_id,
        user_id=job.user_id,
    )
    process_video_job.delay(new_job.id, options)
    return JobOut.from_job(new_job)


def _group_output_files(job: Job) -> JobFilesOut:
    output_dir = Path(job.output_dir)
    stem = Path(job.input_path).stem
    if not output_dir.exists():
        return JobFilesOut(videos=[], subtitles=[])
    files = [
        f
        for f in sorted(output_dir.glob("*.*"))
        if f.is_file() and not f.name.endswith(_INTERNAL_SUFFIXES)
    ]

    videos = []
    subtitle_files = []
    for f in files:
        if ".dubbed." in f.name and f.suffix.lower() in _VIDEO_SUFFIXES:
            lang = f.name.removeprefix(f"{stem}.").split(".")[0]
            videos.append(VideoOut(name=f.name, language=lang, size_bytes=f.stat().st_size))
        else:
            subtitle_files.append(f)

    groups: dict[str, list[Path]] = {}
    for f in subtitle_files:
        rest = f.name.removeprefix(f"{stem}.")
        lang = rest.split(".")[0] if "." in rest else "goc"
        groups.setdefault(lang, []).append(f)

    subtitles = []
    for lang, group in groups.items():
        label = "Phụ đề gốc" if lang == "goc" else f"Phụ đề đã dịch ({lang})"
        txt = next((f for f in group if f.suffix == ".txt"), None)
        subtitles.append(
            SubtitleGroupOut(
                language=lang,
                label=label,
                files=[
                    FileOut(
                        name=f.name,
                        format=f.suffix.removeprefix(".").upper(),
                        size_bytes=f.stat().st_size,
                    )
                    for f in sorted(group, key=lambda x: x.suffix)
                ],
                preview_text=txt.read_text(encoding="utf-8") if txt else None,
            )
        )
    return JobFilesOut(videos=videos, subtitles=subtitles)


@router.get("/{job_id}/files", response_model=JobFilesOut)
def list_files(job_id: str, user: AuthUser = Depends(get_current_user)) -> JobFilesOut:
    return _group_output_files(_get_owned_job(job_id, user))


@router.get("/{job_id}/files/{name}")
def download_file(
    job_id: str, name: str, user: AuthUser = Depends(get_current_user)
) -> FileResponse:
    job = _get_owned_job(job_id, user)
    output_dir = Path(job.output_dir)
    # Chong path traversal: chi chap nhan ten file nam TRUC TIEP trong
    # output_dir (so khop voi danh sach that, khong ghep duong dan tu input).
    target = next((f for f in output_dir.glob("*.*") if f.name == name and f.is_file()), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy file")
    media_type = "video/mp4" if target.suffix in (".mp4", ".mkv") else None
    return FileResponse(target, media_type=media_type, filename=target.name)
