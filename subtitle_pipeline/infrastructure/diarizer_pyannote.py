"""Adapter cho pyannote speaker diarization. Can HF_TOKEN va da accept license
cua pyannote/speaker-diarization-3.1 + pyannote/segmentation-3.0 tren HuggingFace
(xem HANDOFF.md muc 5)."""

import sys
from pathlib import Path

from subtitle_pipeline.domain.models import SpeakerTurn
from subtitle_pipeline.infrastructure.gpu import release_gpu_memory


def _patch_speechbrain_lazy_import_for_windows() -> None:
    """Avoid optional k2 lazy import when inspect.stack scans modules on Windows."""
    try:
        from speechbrain.utils.importutils import LazyModule
    except Exception:
        return

    if getattr(LazyModule, "_subtitle_studio_windows_patch", False):
        return

    original_ensure_module = LazyModule.ensure_module

    def ensure_module(self, stacklevel: int):
        try:
            filename = sys._getframe(stacklevel + 1).f_code.co_filename
        except ValueError:
            filename = ""
        if filename.replace("\\", "/").endswith("/inspect.py"):
            raise AttributeError()
        return original_ensure_module(self, stacklevel)

    LazyModule.ensure_module = ensure_module
    LazyModule._subtitle_studio_windows_patch = True


class PyannoteDiarizer:
    def __init__(self, hf_token: str | None, device: str):
        if not hf_token:
            raise ValueError("HF_TOKEN is required for pyannote diarization")
        self._hf_token = hf_token
        self._device = device
        self._pipeline = None

    def __enter__(self) -> "PyannoteDiarizer":
        _patch_speechbrain_lazy_import_for_windows()
        from pyannote.audio import Pipeline

        self._pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1", use_auth_token=self._hf_token
        )
        if self._device == "cuda":
            import torch

            self._pipeline.to(torch.device("cuda"))
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._pipeline = None
        release_gpu_memory()

    def diarize(self, audio_path: Path) -> list[SpeakerTurn]:
        diarization = self._pipeline(str(audio_path))
        return [
            SpeakerTurn(start=turn.start, end=turn.end, speaker=speaker)
            for turn, _, speaker in diarization.itertracks(yield_label=True)
        ]
