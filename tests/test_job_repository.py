"""Test JobRepository bang SQLite in-memory - khong can Postgres that chay."""
from pathlib import Path

from app.db.models import JobStatus
from app.db.session import make_session_factory
from app.jobs.repository import JobRepository


def _make_repo() -> JobRepository:
    return JobRepository(session_factory=make_session_factory("sqlite:///:memory:"))


def test_create_and_get_job():
    repo = _make_repo()

    job = repo.create(
        filename="video.mp4", input_path=Path("in.mp4"), output_dir=Path("out"), user_id="user-1"
    )
    fetched = repo.get(job.id)

    assert fetched is not None
    assert fetched.filename == "video.mp4"
    assert fetched.status == JobStatus.QUEUED
    assert fetched.user_id == "user-1"


def test_get_unknown_job_returns_none():
    repo = _make_repo()

    assert repo.get("does-not-exist") is None


def test_update_status_changes_stage_and_status():
    repo = _make_repo()
    job = repo.create(
        filename="video.mp4", input_path=Path("in.mp4"), output_dir=Path("out"), user_id="user-1"
    )

    repo.update_status(job.id, status=JobStatus.RUNNING, stage="transcribe")

    fetched = repo.get(job.id)
    assert fetched.status == JobStatus.RUNNING
    assert fetched.stage == "transcribe"


def test_update_status_on_unknown_job_is_a_noop():
    repo = _make_repo()

    repo.update_status("does-not-exist", status=JobStatus.RUNNING)  # khong raise


def test_list_all_returns_created_jobs():
    repo = _make_repo()
    first = repo.create(
        filename="a.mp4", input_path=Path("a.mp4"), output_dir=Path("a"), user_id="user-1"
    )
    second = repo.create(
        filename="b.mp4", input_path=Path("b.mp4"), output_dir=Path("b"), user_id="user-2"
    )

    jobs = repo.list_all()

    assert {j.id for j in jobs} == {first.id, second.id}


def test_list_by_user_only_returns_that_users_jobs():
    repo = _make_repo()
    own_job = repo.create(
        filename="a.mp4", input_path=Path("a.mp4"), output_dir=Path("a"), user_id="user-1"
    )
    repo.create(
        filename="b.mp4", input_path=Path("b.mp4"), output_dir=Path("b"), user_id="user-2"
    )

    jobs = repo.list_by_user("user-1")

    assert [j.id for j in jobs] == [own_job.id]
