"""Abstraction luu file: local filesystem (dev) hoac S3/MinIO (production),
chon qua bien moi truong STORAGE_BACKEND.

LUU Y: day la ha tang moi cho Phase 8, CHUA duoc noi vao Upload/Editor/Celery
task (cac cho do van dung Path filesystem truc tiep, ve hanh vi tuong duong
LocalStorage). Muon chuyen sang S3 that trong production can sua cac diem do
de goi qua Storage thay vi Path truc tiep - xem HANDOFF.md Phase 8.
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class Storage(Protocol):
    def save(self, relative_path: str, data: bytes) -> None: ...
    def read(self, relative_path: str) -> bytes: ...
    def exists(self, relative_path: str) -> bool: ...


@dataclass
class LocalStorage:
    root: Path

    def save(self, relative_path: str, data: bytes) -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def read(self, relative_path: str) -> bytes:
        return (self.root / relative_path).read_bytes()

    def exists(self, relative_path: str) -> bool:
        return (self.root / relative_path).exists()


@dataclass
class S3Storage:
    bucket: str
    prefix: str = ""

    def _key(self, relative_path: str) -> str:
        return f"{self.prefix}{relative_path}"

    def save(self, relative_path: str, data: bytes) -> None:
        import boto3

        boto3.client("s3").put_object(Bucket=self.bucket, Key=self._key(relative_path), Body=data)

    def read(self, relative_path: str) -> bytes:
        import boto3

        obj = boto3.client("s3").get_object(Bucket=self.bucket, Key=self._key(relative_path))
        return obj["Body"].read()

    def exists(self, relative_path: str) -> bool:
        import boto3
        from botocore.exceptions import ClientError

        try:
            boto3.client("s3").head_object(Bucket=self.bucket, Key=self._key(relative_path))
            return True
        except ClientError:
            return False


def get_storage(storage_dir: Path) -> Storage:
    backend = os.environ.get("STORAGE_BACKEND", "local")
    if backend == "s3":
        bucket = os.environ.get("S3_BUCKET")
        if not bucket:
            raise RuntimeError("S3_BUCKET chua duoc set - xem .env.example")
        return S3Storage(bucket=bucket, prefix=os.environ.get("S3_PREFIX", ""))
    return LocalStorage(root=storage_dir)
