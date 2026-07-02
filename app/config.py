"""Cau hinh app (thu muc luu file upload/output). Doc tu bien moi truong."""
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppConfig:
    storage_dir: Path

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(storage_dir=Path(os.environ.get("STORAGE_DIR", "storage")))
