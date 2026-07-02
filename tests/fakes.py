"""Fake adapter dung de test TranscriptionPipeline ma khong can torch/faster-whisper/
whisperx/pyannote/deepfilternet cai dat that su. Cac module application/, domain/,
export/ khong import AI libs o top-level nen dieu nay hoat dong duoc kha ca trong
moi truong khong co GPU (xem docs/memory/dev-machine-rtx4050.md).
"""

from pathlib import Path

from subtitle_pipeline.domain.models import SpeakerTurn, SubtitleSegment, TranscriptSegment


class FakeDenoiser:
    def __enter__(self) -> "FakeDenoiser":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def denoise(self, input_path: Path, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake-denoised-audio")


class FakeTranscriber:
    def __enter__(self) -> "FakeTranscriber":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def transcribe(self, audio_path: Path) -> tuple[list[TranscriptSegment], str]:
        return (
            [
                TranscriptSegment(start=0.0, end=2.0, text="Xin chao"),
                TranscriptSegment(start=2.0, end=4.0, text="Toi la AI"),
            ],
            "vi",
        )


class FakeAligner:
    def __enter__(self) -> "FakeAligner":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def align(self, audio_path: Path, transcript: list[TranscriptSegment]) -> list[SubtitleSegment]:
        return [SubtitleSegment(start=t.start, end=t.end, text=t.text) for t in transcript]


class FakeDiarizer:
    def __enter__(self) -> "FakeDiarizer":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def diarize(self, audio_path: Path) -> list[SpeakerTurn]:
        return [
            SpeakerTurn(start=0.0, end=2.0, speaker="SPEAKER_00"),
            SpeakerTurn(start=2.0, end=4.0, speaker="SPEAKER_01"),
        ]
