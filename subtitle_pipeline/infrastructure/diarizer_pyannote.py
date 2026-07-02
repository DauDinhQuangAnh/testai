"""Adapter cho pyannote speaker diarization. Can HF_TOKEN va da accept license
cua pyannote/speaker-diarization-3.1 + pyannote/segmentation-3.0 tren HuggingFace
(xem HANDOFF.md muc 5)."""
from pathlib import Path

from subtitle_pipeline.domain.models import SpeakerTurn
from subtitle_pipeline.infrastructure.gpu import release_gpu_memory


class PyannoteDiarizer:
    def __init__(self, hf_token: str | None, device: str):
        if not hf_token:
            raise ValueError("HF_TOKEN is required for pyannote diarization")
        self._hf_token = hf_token
        self._device = device
        self._pipeline = None

    def __enter__(self) -> "PyannoteDiarizer":
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
