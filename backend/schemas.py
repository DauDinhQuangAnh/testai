"""Pydantic schema cho API - FE (frontend/src/lib/types.ts) phai khop cac
truong nay."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.db.models import Job
from app.jobs.stages import stage_progress


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class LoginIn(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    created_at: datetime | None = None


class TokenOut(BaseModel):
    token: str
    role: str
    user: UserOut


class JobOut(BaseModel):
    id: str
    user_id: str | None
    filename: str
    status: str
    stage: str | None
    stage_label: str
    progress: float  # 0..1
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_job(cls, job: Job) -> "JobOut":
        fraction, label = stage_progress(job.stage)
        if job.status == "done":
            fraction, label = 1.0, "Hoàn thành"
        return cls(
            id=job.id,
            user_id=job.user_id,
            filename=job.filename,
            status=job.status.value,
            stage=job.stage,
            stage_label=label,
            progress=fraction,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )


class FileOut(BaseModel):
    name: str
    format: str
    size_bytes: int


class SubtitleGroupOut(BaseModel):
    language: str  # "goc" = phu de goc chua dich
    label: str
    files: list[FileOut]
    preview_text: str | None = None


class VideoOut(BaseModel):
    name: str
    language: str
    size_bytes: int


class JobFilesOut(BaseModel):
    videos: list[VideoOut]
    subtitles: list[SubtitleGroupOut]


class VoiceSampleIn(BaseModel):
    language: str
    voice: str
    rate_percent: int = 0
    pitch_hz: int = 0


class AdminUserOut(BaseModel):
    id: str
    email: str
    created_at: datetime
    job_count: int
