from pathlib import Path

from app.jobs.service import create_download_job


class FakeTask:
    calls = []

    @staticmethod
    def delay(*args):
        FakeTask.calls.append(args)


class FakeRepo:
    created = []

    def create(self, **kwargs):
        FakeRepo.created.append(kwargs)


def test_create_download_job_writes_config_and_enqueues(monkeypatch, tmp_path):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    FakeTask.calls = []
    FakeRepo.created = []

    job_id = create_download_job(
        url="https://www.youtube.com/watch?v=abc",
        title="Demo Video",
        quality="720p",
        telegram={"chat_id": 123, "notify_email": "user@test.com"},
        enqueue_task=FakeTask,
        job_repo_factory=FakeRepo,
    )

    job_dir = tmp_path / "storage" / job_id
    assert (job_dir / "job_config.json").exists()
    assert FakeRepo.created[0]["filename"] == "Demo Video.mp4"
    assert Path(FakeRepo.created[0]["input_path"]).name == "Demo Video.mp4"
    assert FakeTask.calls[0][0] == job_id
    assert FakeTask.calls[0][1]["source"]["input_mode"] == "download"
    assert FakeTask.calls[0][1]["telegram"]["chat_id"] == 123
