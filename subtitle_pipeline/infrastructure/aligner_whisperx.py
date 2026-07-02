"""Adapter cho WhisperX alignment - can chinh timestamp o muc tu dua tren
transcript tho tu Faster-Whisper."""

from pathlib import Path

from subtitle_pipeline.domain.models import SubtitleSegment, TranscriptSegment
from subtitle_pipeline.infrastructure.gpu import release_gpu_memory


class WhisperXAligner:
    def __init__(self, language: str, device: str):
        self._language = language
        self._device = device
        self._model = None
        self._metadata = None

    def __enter__(self) -> "WhisperXAligner":
        import whisperx

        self._model, self._metadata = whisperx.load_align_model(
            language_code=self._language, device=self._device
        )
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._model = None
        self._metadata = None
        release_gpu_memory()

    def align(self, audio_path: Path, transcript: list[TranscriptSegment]) -> list[SubtitleSegment]:
        import whisperx

        raw_segments = [{"start": t.start, "end": t.end, "text": t.text} for t in transcript]
        result = whisperx.align(
            raw_segments, self._model, self._metadata, str(audio_path), self._device
        )
        return [
            SubtitleSegment(start=seg["start"], end=seg["end"], text=seg["text"])
            for seg in result["segments"]
        ]
