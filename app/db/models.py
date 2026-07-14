"""ORM model: User (tai khoan cho UI React - xem backend/), Job (yeu cau tao
phu de/long tieng). Auth duoc them LAI ngay 2026-07-03 khi chuyen UI tu
Streamlit sang React + FastAPI (xem HANDOFF.md) - job cu tao truoc do co
`user_id=NULL`, chi admin nhin thay.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class JobStatus(enum.StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class CustomVoice(Base):
    """1 giong long tieng nguoi dung tu clone (doc mau 1 doan, luu file
    tham chieu) - xem `subtitle_pipeline/infrastructure/tts_vieneu.py` +
    HANDOFF.md muc 6p. Khong luu speaker embedding (numpy array) vao DB - de
    don gian, `VieNeuCloneSynthesizer` tu ma hoa lai `ref_audio_path` moi
    lan dung (1 lan/job, khong phai 1 lan/segment)."""

    __tablename__ = "custom_voices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36))
    name: Mapped[str] = mapped_column(String(255))
    ref_audio_path: Mapped[str] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    filename: Mapped[str] = mapped_column(String(255))
    input_path: Mapped[str] = mapped_column(String(1024))
    output_dir: Mapped[str] = mapped_column(String(1024))
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.QUEUED)
    stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
