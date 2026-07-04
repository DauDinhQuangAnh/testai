"""Test backend FastAPI bang TestClient + SQLite in-memory - khong can
Postgres/Redis/Celery that (monkeypatch `process_video_job.delay`).
"""

import io
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

import backend.db as backend_db
from app.db.models import Base
from backend.main import app


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
    yield test_client
    backend_db.set_session_factory(None)


def _register(client, email="a@test.com", password="secret1") -> dict:
    res = client.post("/api/auth/register", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_upload_job(client, token: str) -> dict:
    options = {"source": {"url": None}, "dubbing": {"enabled": False}}
    res = client.post(
        "/api/jobs",
        data={"options": json.dumps(options)},
        files={"file": ("video.mp4", io.BytesIO(b"fake-video-bytes"), "video/mp4")},
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


def test_create_url_job_without_file(client):
    token = _register(client)["token"]
    options = {"source": {"url": "https://youtu.be/abc"}, "dubbing": {"enabled": True}}

    res = client.post(
        "/api/jobs", data={"options": json.dumps(options)}, headers=_auth_headers(token)
    )

    assert res.status_code == 200
    assert res.json()["filename"] == "https://youtu.be/abc"


def test_create_job_without_file_or_url_rejected(client):
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
