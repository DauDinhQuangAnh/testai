"""Cau hinh pipeline, doc tu bien moi truong (.env) de de dang doi model size
giua dev (VRAM han che, xem docs/memory/dev-machine-rtx4050.md) va production.
"""

import os
from dataclasses import dataclass


@dataclass
class PipelineConfig:
    whisper_model: str = "medium"
    whisper_compute_type: str = "int8_float16"
    device: str = "cuda"
    language: str = "vi"
    hf_token: str | None = None

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        return cls(
            whisper_model=os.environ.get("WHISPER_MODEL", "medium"),
            whisper_compute_type=os.environ.get("WHISPER_COMPUTE_TYPE", "int8_float16"),
            device=os.environ.get("PIPELINE_DEVICE", "cuda"),
            language=os.environ.get("PIPELINE_LANGUAGE", "vi"),
            hf_token=os.environ.get("HF_TOKEN"),
        )
