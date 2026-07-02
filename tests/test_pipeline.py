"""Test orchestration logic cua TranscriptionPipeline bang fake adapter (khong
can torch/faster-whisper/whisperx/pyannote/deepfilternet cai that)."""
from pathlib import Path

import pytest

from subtitle_pipeline.application.pipeline import PipelineStageError, TranscriptionPipeline
from subtitle_pipeline.config import PipelineConfig
from tests.fakes import FakeAligner, FakeDenoiser, FakeDiarizer, FakeTranscriber


def _fake_extract_audio(input_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(b"fake-raw-audio")


def _make_pipeline(tmp_path: Path, transcriber_factory=None) -> TranscriptionPipeline:
    return TranscriptionPipeline(
        config=PipelineConfig(),
        work_dir=tmp_path / "work",
        denoiser_factory=lambda: FakeDenoiser(),
        transcriber_factory=transcriber_factory or (lambda: FakeTranscriber()),
        aligner_factory=lambda: FakeAligner(),
        diarizer_factory=lambda: FakeDiarizer(),
    )


def test_run_merges_speaker_into_segments(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "subtitle_pipeline.application.pipeline.extract_audio", _fake_extract_audio
    )
    pipeline = _make_pipeline(tmp_path)

    result = pipeline.run(tmp_path / "input.mp4")

    assert [seg.speaker for seg in result] == ["SPEAKER_00", "SPEAKER_01"]
    assert result[0].text == "Xin chao"


def test_stage_failure_wrapped_in_pipeline_stage_error(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "subtitle_pipeline.application.pipeline.extract_audio", _fake_extract_audio
    )

    class BrokenTranscriber(FakeTranscriber):
        def transcribe(self, audio_path):
            raise RuntimeError("model download failed")

    pipeline = _make_pipeline(tmp_path, transcriber_factory=lambda: BrokenTranscriber())

    with pytest.raises(PipelineStageError) as exc_info:
        pipeline.run(tmp_path / "input.mp4")

    assert exc_info.value.stage == "transcribe"


def test_run_invokes_on_stage_callback_in_order(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "subtitle_pipeline.application.pipeline.extract_audio", _fake_extract_audio
    )
    pipeline = _make_pipeline(tmp_path)
    stages: list[str] = []

    pipeline.run(tmp_path / "input.mp4", on_stage=stages.append)

    assert stages == ["extract_audio", "denoise", "transcribe", "align", "diarize", "merge"]
