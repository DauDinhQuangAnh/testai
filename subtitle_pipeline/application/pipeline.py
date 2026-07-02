"""Orchestrator chinh cua AI pipeline: extract -> denoise -> transcribe -> align
-> diarize -> merge speaker. Moi adapter la context manager, load model khi
enter va giai phong VRAM khi exit (xem infrastructure/gpu.py) - phu hop rang
buoc VRAM han che cua may dev (docs/memory/dev-machine-rtx4050.md).

Pipeline chi phu thuoc vao Protocol (domain/ports.py), khong import truc tiep
thu vien AI o day - adapter that duoc tao qua factory (mac dinh) hoac inject khi
test (xem tests/fakes.py, tests/test_pipeline.py).

LUU Y RUI RO: Phase 1 feasibility spike chua co ket qua do tren may dev that khi
module nay duoc viet (nguoi dung chon lam Phase 2 truoc). Giai phong VRAM trong
CUNG 1 process (gc.collect + torch.cuda.empty_cache) it dam bao hon cach do
subprocess rieng cua Phase 1 - CAN chay thu CLI nay tren may dev that de xac
nhan khong OOM giua cac buoc, dac biet la buoc transcribe (large-v3) roi den
align/diarize. Xem HANDOFF.md muc "Van de dang mo".
"""
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from subtitle_pipeline.application.merge import merge_speakers
from subtitle_pipeline.config import PipelineConfig
from subtitle_pipeline.domain.models import SubtitleSegment
from subtitle_pipeline.domain.ports import Aligner, Denoiser, Diarizer, Transcriber
from subtitle_pipeline.infrastructure.aligner_whisperx import WhisperXAligner
from subtitle_pipeline.infrastructure.audio import extract_audio
from subtitle_pipeline.infrastructure.denoiser_deepfilternet import DeepFilterNetDenoiser
from subtitle_pipeline.infrastructure.diarizer_pyannote import PyannoteDiarizer
from subtitle_pipeline.infrastructure.transcriber_faster_whisper import FasterWhisperTranscriber


class PipelineStageError(RuntimeError):
    def __init__(self, stage: str, cause: Exception):
        super().__init__(f"Pipeline stage '{stage}' failed: {cause}")
        self.stage = stage
        self.cause = cause


@dataclass
class TranscriptionPipeline:
    config: PipelineConfig
    work_dir: Path
    denoiser_factory: Callable[[], Denoiser] | None = None
    transcriber_factory: Callable[[], Transcriber] | None = None
    aligner_factory: Callable[[], Aligner] | None = None
    diarizer_factory: Callable[[], Diarizer] | None = None

    def __post_init__(self) -> None:
        self.denoiser_factory = self.denoiser_factory or (lambda: DeepFilterNetDenoiser())
        self.transcriber_factory = self.transcriber_factory or (
            lambda: FasterWhisperTranscriber(
                self.config.whisper_model, self.config.whisper_compute_type, self.config.device
            )
        )
        self.aligner_factory = self.aligner_factory or (
            lambda: WhisperXAligner(self.config.language, self.config.device)
        )
        self.diarizer_factory = self.diarizer_factory or (
            lambda: PyannoteDiarizer(self.config.hf_token, self.config.device)
        )

    def run(
        self, input_path: Path, on_stage: Callable[[str], None] | None = None
    ) -> list[SubtitleSegment]:
        def notify(name: str) -> None:
            if on_stage is not None:
                on_stage(name)

        self.work_dir.mkdir(parents=True, exist_ok=True)

        raw_audio = self.work_dir / "audio_16k.wav"
        notify("extract_audio")
        self._stage("extract_audio", extract_audio, input_path, raw_audio)

        denoised_audio = self.work_dir / "audio_denoised.wav"
        notify("denoise")
        with self.denoiser_factory() as denoiser:
            self._stage("denoise", denoiser.denoise, raw_audio, denoised_audio)

        notify("transcribe")
        with self.transcriber_factory() as transcriber:
            transcript = self._stage("transcribe", transcriber.transcribe, denoised_audio)

        notify("align")
        with self.aligner_factory() as aligner:
            aligned = self._stage("align", aligner.align, denoised_audio, transcript)

        notify("diarize")
        with self.diarizer_factory() as diarizer:
            speaker_turns = self._stage("diarize", diarizer.diarize, denoised_audio)

        notify("merge")
        return merge_speakers(aligned, speaker_turns)

    @staticmethod
    def _stage(name: str, func: Callable, *args):
        try:
            return func(*args)
        except Exception as exc:
            raise PipelineStageError(name, exc) from exc
