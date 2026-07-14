"""Test backend FastAPI bang TestClient + SQLite in-memory - khong can
Postgres/Redis/Celery that (monkeypatch `process_video_job.delay`).
"""

import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

import backend.db as backend_db
from app.db.models import Base, JobStatus
from backend.main import app
from backend.share_links import create_file_share_token
from subtitle_pipeline.infrastructure.downloader_ytdlp import QualityOption, VideoMetadata


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # SQLite in-memory DUY NHAT 1 connection (StaticPool) de moi session cung
    # nhin thay schema/data - sqlite::memory: binh thuong tao DB moi mỗi
    # connection.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    backend_db.set_session_factory(sessionmaker(bind=engine, expire_on_commit=False))

    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    monkeypatch.setenv("ADMIN_EMAIL", "admin@test")
    monkeypatch.setenv("ADMIN_PASSWORD", "admin-secret")

    enqueued: list[tuple] = []
    monkeypatch.setattr(
        "backend.routers.jobs.process_video_job",
        type("FakeTask", (), {"delay": staticmethod(lambda *a: enqueued.append(a))}),
    )

    test_client = TestClient(app)
    test_client.enqueued = enqueued
    test_client.storage_dir = tmp_path / "storage"
    yield test_client
    backend_db.set_session_factory(None)


def _register(client, email="a@test.com", password="secret1") -> dict:
    res = client.post("/api/auth/register", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_upload_job(client, token: str) -> dict:
    options = {"dubbing": {"enabled": False}}
    res = client.post(
        "/api/jobs",
        data={"options": json.dumps(options)},
        files={"file": ("video.mp4", io.BytesIO(b"fake-video-bytes"), "video/mp4")},
        headers=_auth_headers(token),
    )
    assert res.status_code == 200, res.text
    return res.json()


def _stub_ffmpeg_and_probe(monkeypatch, seconds: float = 10.0) -> None:
    """`POST /voices` goi ffmpeg that + do do dai file that - stub ca 2 de
    test khong can ffmpeg/audio that (xem
    subtitle_pipeline/infrastructure/tts_vieneu.py: da spike THAT rieng,
    xem HANDOFF.md muc 6p)."""
    monkeypatch.setattr(
        "backend.routers.voices.subprocess.run",
        lambda cmd, **kw: Path(cmd[-1]).write_bytes(b"fake wav"),
    )
    monkeypatch.setattr("backend.routers.voices.probe_reference_seconds", lambda p: seconds)


def _create_voice(client, token: str, name: str = "Giọng của tôi") -> dict:
    res = client.post(
        "/api/voices",
        data={"name": name},
        files={"file": ("sample.webm", io.BytesIO(b"fake-audio-bytes"), "audio/webm")},
        headers=_auth_headers(token),
    )
    assert res.status_code == 200, res.text
    return res.json()


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_register_login_me_roundtrip(client):
    registered = _register(client)
    assert registered["role"] == "user"

    login = client.post(
        "/api/auth/login", json={"email": "a@test.com", "password": "secret1"}
    ).json()
    me = client.get("/api/auth/me", headers=_auth_headers(login["token"])).json()

    assert me["email"] == "a@test.com"


def test_register_duplicate_email_conflicts(client):
    _register(client)

    res = client.post("/api/auth/register", json={"email": "a@test.com", "password": "secret1"})

    assert res.status_code == 409


def test_login_wrong_password_rejected(client):
    _register(client)

    res = client.post("/api/auth/login", json={"email": "a@test.com", "password": "wrong!"})

    assert res.status_code == 401


def test_admin_login_uses_env_credentials(client):
    res = client.post("/api/auth/login", json={"email": "admin@test", "password": "admin-secret"})

    assert res.status_code == 200
    assert res.json()["role"] == "admin"


def test_create_upload_job_enqueues_task(client):
    token = _register(client)["token"]

    job = _create_upload_job(client, token)

    assert job["status"] == "queued"
    assert client.enqueued and client.enqueued[0][0] == job["id"]


def test_analyze_source_returns_video_metadata(client, monkeypatch):
    token = _register(client)["token"]

    monkeypatch.setattr(
        "backend.routers.jobs.analyze_video",
        lambda url: VideoMetadata(
            url=url,
            title="Demo video",
            thumbnail="https://example.test/thumb.jpg",
            duration=65,
            uploader="Uploader",
            source="Youtube",
            qualities=[QualityOption("best", "Tot nhat", "bestvideo+bestaudio/best")],
        ),
    )

    res = client.post(
        "/api/jobs/source/analyze",
        json={"url": "https://www.youtube.com/watch?v=abc123"},
        headers=_auth_headers(token),
    )

    assert res.status_code == 200, res.text
    assert res.json()["title"] == "Demo video"
    assert res.json()["qualities"][0]["id"] == "best"


def test_create_download_job_enqueues_task_without_upload(client):
    token = _register(client)["token"]
    options = {
        "source": {
            "download": {
                "url": "https://www.youtube.com/watch?v=abc123",
                "quality": "720p",
                "title": "Demo video",
            }
        },
        "dubbing": {"enabled": False},
    }

    res = client.post(
        "/api/jobs",
        data={"options": json.dumps(options)},
        headers=_auth_headers(token),
    )

    assert res.status_code == 200, res.text
    job = res.json()
    assert job["filename"] == "Demo video.mp4"
    assert client.enqueued and client.enqueued[0][0] == job["id"]
    assert client.enqueued[0][1]["source"]["input_mode"] == "download"


def test_create_job_without_file_rejected(client):
    token = _register(client)["token"]

    res = client.post("/api/jobs", data={"options": json.dumps({})}, headers=_auth_headers(token))

    assert res.status_code == 400


def test_user_cannot_see_other_users_job(client):
    token_a = _register(client, "a@test.com")["token"]
    token_b = _register(client, "b@test.com")["token"]
    job = _create_upload_job(client, token_a)

    assert client.get("/api/jobs", headers=_auth_headers(token_b)).json() == []
    assert client.get(f"/api/jobs/{job['id']}", headers=_auth_headers(token_b)).status_code == 404


def test_admin_sees_all_jobs(client):
    token_a = _register(client, "a@test.com")["token"]
    _create_upload_job(client, token_a)
    admin_token = client.post(
        "/api/auth/login", json={"email": "admin@test", "password": "admin-secret"}
    ).json()["token"]

    jobs = client.get("/api/jobs", headers=_auth_headers(admin_token)).json()

    assert len(jobs) == 1


def test_normal_user_cannot_access_admin_routes(client):
    token = _register(client)["token"]

    res = client.get("/api/admin/users", headers=_auth_headers(token))

    assert res.status_code == 403


def test_admin_lists_users_with_job_count(client):
    token = _register(client)["token"]
    _create_upload_job(client, token)
    admin_token = client.post(
        "/api/auth/login", json={"email": "admin@test", "password": "admin-secret"}
    ).json()["token"]

    users = client.get("/api/admin/users", headers=_auth_headers(admin_token)).json()

    assert len(users) == 1
    assert users[0]["job_count"] == 1


def test_refresh_cookies_requires_admin(client):
    token = _register(client)["token"]

    res = client.post("/api/admin/refresh-cookies", headers=_auth_headers(token))

    assert res.status_code == 403


def test_refresh_cookies_calls_playwright_helper(client, monkeypatch, tmp_path):
    admin_token = client.post(
        "/api/auth/login", json={"email": "admin@test", "password": "admin-secret"}
    ).json()["token"]
    cookies_path = tmp_path / "cookies.txt"
    monkeypatch.setenv("YTDLP_COOKIES_FILE", str(cookies_path))
    monkeypatch.setattr("backend.routers.admin.refresh_cookies", lambda path: 7)

    res = client.post("/api/admin/refresh-cookies", headers=_auth_headers(admin_token))

    assert res.status_code == 200
    assert res.json() == {"cookie_count": 7, "path": str(cookies_path)}


def test_refresh_cookies_reports_error_as_502(client, monkeypatch):
    admin_token = client.post(
        "/api/auth/login", json={"email": "admin@test", "password": "admin-secret"}
    ).json()["token"]

    def _boom(path):
        raise RuntimeError("chua chay --setup lan nao")

    monkeypatch.setattr("backend.routers.admin.refresh_cookies", _boom)

    res = client.post("/api/admin/refresh-cookies", headers=_auth_headers(admin_token))

    assert res.status_code == 502
    assert "chua chay --setup" in res.json()["detail"]


def test_delete_job_removes_record(client):
    token = _register(client)["token"]
    job = _create_upload_job(client, token)

    res = client.delete(f"/api/jobs/{job['id']}", headers=_auth_headers(token))

    assert res.status_code == 200
    assert client.get("/api/jobs", headers=_auth_headers(token)).json() == []


def test_meta_languages_and_voices(client):
    langs = client.get("/api/meta/languages").json()
    voices = client.get("/api/meta/voices/vi").json()

    assert "vi" in langs["targets"]
    assert any(v["recommended"] for v in voices)


def test_download_accepts_token_query_param(client, tmp_path):
    token = _register(client)["token"]
    job = _create_upload_job(client, token)
    # Gia lap worker da xuat 1 file ket qua.
    job_detail = client.get(f"/api/jobs/{job['id']}", headers=_auth_headers(token)).json()
    assert job_detail["id"] == job["id"]

    res = client.get(f"/api/jobs/{job['id']}/files", headers=_auth_headers(token))
    assert res.json() == {"videos": [], "subtitles": []}

    # Token qua query param (cho <video>/<a download> khong gui duoc header).
    res = client.get(f"/api/jobs/{job['id']}/files?token={token}")
    assert res.status_code == 200


def test_public_download_requires_signed_file_token(client, monkeypatch):
    monkeypatch.setenv("PUBLIC_LINK_SECRET", "test-public-secret")
    token = _register(client)["token"]
    job = _create_upload_job(client, token)
    output_dir = client.storage_dir / job["id"] / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = "video.vi.dubbed.mp4"
    (output_dir / filename).write_bytes(b"video")

    share_token = create_file_share_token(job["id"], filename)
    ok = client.get(f"/api/public/jobs/{job['id']}/files/{filename}?token={share_token}")
    denied = client.get(f"/api/public/jobs/{job['id']}/files/{filename}?token=bad")

    assert ok.status_code == 200
    assert ok.content == b"video"
    assert denied.status_code == 403


def test_job_files_only_classifies_real_dubbed_videos_as_videos(client):
    token = _register(client)["token"]
    job = _create_upload_job(client, token)
    stem = "video"
    output_dir = client.storage_dir / job["id"] / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"{stem}.vi.dubbed.mp4").write_bytes(b"video")
    (output_dir / f"{stem}.vi.ass").write_text("subtitle", encoding="utf-8")
    (output_dir / f"{stem}.vi.json").write_text("[]", encoding="utf-8")
    (output_dir / f"{stem}.vi.srt").write_text("subtitle", encoding="utf-8")

    res = client.get(f"/api/jobs/{job['id']}/files", headers=_auth_headers(token))

    assert res.status_code == 200
    body = res.json()
    assert [video["name"] for video in body["videos"]] == [f"{stem}.vi.dubbed.mp4"]
    assert body["subtitles"]


def test_get_subtitles_returns_segments(client):
    token = _register(client)["token"]
    job = _create_upload_job(client, token)
    output_dir = client.storage_dir / job["id"] / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "video.json").write_text(
        json.dumps([{"start": 0.0, "end": 1.5, "text": "Xin chào", "speaker": None}]),
        encoding="utf-8",
    )

    res = client.get(f"/api/jobs/{job['id']}/subtitles/goc", headers=_auth_headers(token))

    assert res.status_code == 200
    assert res.json() == [{"start": 0.0, "end": 1.5, "text": "Xin chào", "speaker": None}]


def test_get_subtitles_missing_language_returns_404(client):
    token = _register(client)["token"]
    job = _create_upload_job(client, token)

    res = client.get(f"/api/jobs/{job['id']}/subtitles/vi", headers=_auth_headers(token))

    assert res.status_code == 404


def test_update_subtitles_rewrites_all_formats(client):
    token = _register(client)["token"]
    job = _create_upload_job(client, token)
    output_dir = client.storage_dir / job["id"] / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "video.json").write_text("[]", encoding="utf-8")

    body = {"segments": [{"start": 0.0, "end": 2.0, "text": "Sửa lại", "speaker": "SPEAKER_00"}]}
    res = client.put(
        f"/api/jobs/{job['id']}/subtitles/goc", json=body, headers=_auth_headers(token)
    )

    assert res.status_code == 200
    assert res.json() == {"saved": 1}
    assert "Sửa lại" in (output_dir / "video.srt").read_text(encoding="utf-8")
    assert json.loads((output_dir / "video.json").read_text(encoding="utf-8"))[0]["text"] == (
        "Sửa lại"
    )


def test_update_subtitles_missing_language_returns_404(client):
    token = _register(client)["token"]
    job = _create_upload_job(client, token)

    res = client.put(
        f"/api/jobs/{job['id']}/subtitles/vi",
        json={"segments": []},
        headers=_auth_headers(token),
    )

    assert res.status_code == 404


def test_translate_endpoint_enqueues_task_when_job_done(client, monkeypatch):
    token = _register(client)["token"]
    job = _create_upload_job(client, token)
    backend_db.job_repo().update_status(job["id"], status=JobStatus.DONE)
    enqueued = []
    monkeypatch.setattr(
        "backend.routers.jobs.translate_job",
        type("FakeTask", (), {"delay": staticmethod(lambda *a: enqueued.append(a))}),
    )

    res = client.post(
        f"/api/jobs/{job['id']}/translate",
        json={"target_language": "en"},
        headers=_auth_headers(token),
    )

    assert res.status_code == 200
    assert enqueued == [(job["id"], "en")]


def test_translate_endpoint_rejects_job_not_done(client):
    token = _register(client)["token"]
    job = _create_upload_job(client, token)

    res = client.post(
        f"/api/jobs/{job['id']}/translate",
        json={"target_language": "en"},
        headers=_auth_headers(token),
    )

    assert res.status_code == 400


def test_dub_endpoint_enqueues_task_when_job_done(client, monkeypatch):
    token = _register(client)["token"]
    job = _create_upload_job(client, token)
    backend_db.job_repo().update_status(job["id"], status=JobStatus.DONE)
    enqueued = []
    monkeypatch.setattr(
        "backend.routers.jobs.dub_job",
        type("FakeTask", (), {"delay": staticmethod(lambda *a: enqueued.append(a))}),
    )

    res = client.post(
        f"/api/jobs/{job['id']}/dub",
        json={"target_language": "vi", "voice": "vi-VN-HoaiMyNeural", "keep_original_audio": True},
        headers=_auth_headers(token),
    )

    assert res.status_code == 200
    assert enqueued == [(job["id"], "vi", "vi-VN-HoaiMyNeural", True, None)]


def test_original_file_downloads_input(client):
    token = _register(client)["token"]
    job = _create_upload_job(client, token)

    res = client.get(f"/api/jobs/{job['id']}/original", headers=_auth_headers(token))

    assert res.status_code == 200
    assert res.content == b"fake-video-bytes"


def test_create_voice_uploads_and_lists(client, monkeypatch):
    token = _register(client)["token"]
    _stub_ffmpeg_and_probe(monkeypatch)

    voice = _create_voice(client, token)

    assert voice["name"] == "Giọng của tôi"
    listed = client.get("/api/voices", headers=_auth_headers(token)).json()
    assert [v["id"] for v in listed] == [voice["id"]]


def test_create_voice_rejects_too_short_reference(client, monkeypatch):
    token = _register(client)["token"]
    _stub_ffmpeg_and_probe(monkeypatch, seconds=1.0)

    res = client.post(
        "/api/voices",
        data={"name": "Ngắn quá"},
        files={"file": ("sample.webm", io.BytesIO(b"fake-audio"), "audio/webm")},
        headers=_auth_headers(token),
    )

    assert res.status_code == 400


def test_delete_voice_removes_record(client, monkeypatch):
    token = _register(client)["token"]
    _stub_ffmpeg_and_probe(monkeypatch)
    voice = _create_voice(client, token)

    res = client.delete(f"/api/voices/{voice['id']}", headers=_auth_headers(token))

    assert res.status_code == 200
    assert client.get("/api/voices", headers=_auth_headers(token)).json() == []


def test_user_cannot_see_other_users_voices(client, monkeypatch):
    _stub_ffmpeg_and_probe(monkeypatch)
    token_a = _register(client, "a@test.com")["token"]
    token_b = _register(client, "b@test.com")["token"]
    _create_voice(client, token_a)

    assert client.get("/api/voices", headers=_auth_headers(token_b)).json() == []


def test_delete_voice_owned_by_other_user_returns_404(client, monkeypatch):
    _stub_ffmpeg_and_probe(monkeypatch)
    token_a = _register(client, "a@test.com")["token"]
    token_b = _register(client, "b@test.com")["token"]
    voice = _create_voice(client, token_a)

    res = client.delete(f"/api/voices/{voice['id']}", headers=_auth_headers(token_b))

    assert res.status_code == 404


def test_dub_endpoint_accepts_own_custom_voice(client, monkeypatch):
    _stub_ffmpeg_and_probe(monkeypatch)
    token = _register(client)["token"]
    voice = _create_voice(client, token)
    job = _create_upload_job(client, token)
    backend_db.job_repo().update_status(job["id"], status=JobStatus.DONE)
    enqueued = []
    monkeypatch.setattr(
        "backend.routers.jobs.dub_job",
        type("FakeTask", (), {"delay": staticmethod(lambda *a: enqueued.append(a))}),
    )

    res = client.post(
        f"/api/jobs/{job['id']}/dub",
        json={"target_language": "vi", "custom_voice_id": voice["id"]},
        headers=_auth_headers(token),
    )

    assert res.status_code == 200
    assert enqueued == [(job["id"], "vi", None, False, voice["id"])]


def test_dub_endpoint_rejects_voice_owned_by_other_user(client, monkeypatch):
    _stub_ffmpeg_and_probe(monkeypatch)
    token_a = _register(client, "a@test.com")["token"]
    token_b = _register(client, "b@test.com")["token"]
    voice = _create_voice(client, token_a)
    job = _create_upload_job(client, token_b)
    backend_db.job_repo().update_status(job["id"], status=JobStatus.DONE)

    res = client.post(
        f"/api/jobs/{job['id']}/dub",
        json={"target_language": "vi", "custom_voice_id": voice["id"]},
        headers=_auth_headers(token_b),
    )

    assert res.status_code == 404


def test_create_job_rejects_custom_voice_owned_by_other_user(client, monkeypatch):
    _stub_ffmpeg_and_probe(monkeypatch)
    token_a = _register(client, "a@test.com")["token"]
    token_b = _register(client, "b@test.com")["token"]
    voice = _create_voice(client, token_a)

    options = {"dubbing": {"enabled": True, "custom_voice_id": voice["id"]}}
    res = client.post(
        "/api/jobs",
        data={"options": json.dumps(options)},
        files={"file": ("video.mp4", io.BytesIO(b"fake-video-bytes"), "video/mp4")},
        headers=_auth_headers(token_b),
    )

    assert res.status_code == 404


def test_send_email_rejects_job_not_done(client):
    token = _register(client)["token"]
    job = _create_upload_job(client, token)

    res = client.post(f"/api/jobs/{job['id']}/send-email", headers=_auth_headers(token))

    assert res.status_code == 400


def test_send_email_uses_registered_email(client, monkeypatch):
    token = _register(client, "a@test.com")["token"]
    job = _create_upload_job(client, token)
    backend_db.job_repo().update_status(job["id"], status=JobStatus.DONE)

    sent: list[tuple] = []
    monkeypatch.setattr(
        "backend.routers.jobs.send_job_result_email",
        lambda to_email, job_id, filename: sent.append((to_email, job_id, filename)),
    )

    res = client.post(f"/api/jobs/{job['id']}/send-email", headers=_auth_headers(token))

    assert res.status_code == 200
    assert res.json() == {"sent_to": "a@test.com"}
    assert sent == [("a@test.com", job["id"], "video.mp4")]


def test_send_email_reports_smtp_error_as_502(client, monkeypatch):
    token = _register(client)["token"]
    job = _create_upload_job(client, token)
    backend_db.job_repo().update_status(job["id"], status=JobStatus.DONE)

    def _boom(to_email, job_id, filename):
        raise RuntimeError("SMTP loi")

    monkeypatch.setattr("backend.routers.jobs.send_job_result_email", _boom)

    res = client.post(f"/api/jobs/{job['id']}/send-email", headers=_auth_headers(token))

    assert res.status_code == 502
