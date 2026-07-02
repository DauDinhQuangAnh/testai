"""Test LocalStorage - S3Storage khong test duoc o day vi can AWS credential
that (chi ra soat bang doc code, xem app/storage.py)."""
from pathlib import Path

from app.storage import LocalStorage, get_storage


def test_local_storage_save_and_read(tmp_path: Path):
    storage = LocalStorage(root=tmp_path)

    storage.save("jobs/abc/input.mp4", b"fake-bytes")

    assert storage.exists("jobs/abc/input.mp4")
    assert storage.read("jobs/abc/input.mp4") == b"fake-bytes"


def test_local_storage_exists_false_for_missing_file(tmp_path: Path):
    storage = LocalStorage(root=tmp_path)

    assert not storage.exists("does/not/exist.txt")


def test_get_storage_defaults_to_local(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("STORAGE_BACKEND", raising=False)

    storage = get_storage(tmp_path)

    assert isinstance(storage, LocalStorage)
    assert storage.root == tmp_path
