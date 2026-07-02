"""Repository cho Job - tach truy van DB ra khoi Streamlit pages va Celery task.

Nhan session_factory qua constructor (mac dinh dung Postgres that qua
make_session_factory()) thay vi import thang mot session global - nho vay test
duoc bang SQLite in-memory ma khong can Postgres chay (xem
tests/test_job_repository.py).
"""
import uuid
from collections.abc import Callable, Sequence
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Job, JobStatus
from app.db.session import make_session_factory


class JobRepository:
    def __init__(self, session_factory: Callable[[], Session] | None = None):
        self._session_factory = session_factory or make_session_factory()

    def create(
        self,
        filename: str,
        input_path: Path,
        output_dir: Path,
        user_id: str,
        job_id: str | None = None,
    ) -> Job:
        with self._session_factory() as session:
            job = Job(
                id=job_id or str(uuid.uuid4()),
                user_id=user_id,
                filename=filename,
                input_path=str(input_path),
                output_dir=str(output_dir),
                status=JobStatus.QUEUED,
            )
            session.add(job)
            session.commit()
            session.refresh(job)
            return job

    def get(self, job_id: str) -> Job | None:
        with self._session_factory() as session:
            return session.get(Job, job_id)

    def list_all(self) -> Sequence[Job]:
        with self._session_factory() as session:
            return session.scalars(select(Job).order_by(Job.created_at.desc())).all()

    def list_by_user(self, user_id: str) -> Sequence[Job]:
        with self._session_factory() as session:
            stmt = select(Job).where(Job.user_id == user_id).order_by(Job.created_at.desc())
            return session.scalars(stmt).all()

    def delete(self, job_id: str) -> None:
        with self._session_factory() as session:
            job = session.get(Job, job_id)
            if job is None:
                return
            session.delete(job)
            session.commit()

    def update_status(
        self,
        job_id: str,
        status: JobStatus,
        stage: str | None = None,
        error_message: str | None = None,
    ) -> None:
        with self._session_factory() as session:
            job = session.get(Job, job_id)
            if job is None:
                return
            job.status = status
            if stage is not None:
                job.stage = stage
            if error_message is not None:
                job.error_message = error_message
            session.commit()
