"""Adapter cho Faster-Whisper. Dung vad_filter=True (Silero VAD tich hop san
trong faster-whisper) de loc khoang lang - vi vay pipeline nay KHONG co adapter
Silero VAD rieng (xem quyet dinh trong HANDOFF.md muc "Quyet dinh moi").

model_size/compute_type lay tu PipelineConfig - doi duoc giua dev (vd. "medium")
va production (vd. "large-v3") ma khong sua code, xem config.py va
docs/memory/dev-machine-rtx4050.md (VRAM 6GB khong du cho large-v3 fp16).
"""

from pathlib import Path

from subtitle_pipeline.domain.models import TranscriptSegment
from subtitle_pipeline.infrastructure.gpu import release_gpu_memory


class FasterWhisperTranscriber:
    def __init__(self, model_size: str, compute_type: str, device: str):
        self._model_size = model_size
        self._compute_type = compute_type
        self._device = device
        self._model = None

    def __enter__(self) -> "FasterWhisperTranscriber":
        from faster_whisper import WhisperModel

        self._model = WhisperModel(
            self._model_size, device=self._device, compute_type=self._compute_type
        )
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._model = None
        release_gpu_memory()

    def transcribe(self, audio_path: Path) -> tuple[list[TranscriptSegment], str]:
        # KHONG truyen `language=` - de Faster-Whisper tu auto-detect ngon
        # ngu that cua audio (co the khac PIPELINE_LANGUAGE trong .env, vd.
        # video nguon tieng Anh nhung PIPELINE_LANGUAGE=vi de dinh huong dich
        # cuoi cung sang tieng Viet). `info.language` duoc tra ve cho cac
        # buoc sau (align/dich) dung ngon ngu THAT, xem HANDOFF.md.
        segments, info = self._model.transcribe(str(audio_path), beam_size=5, vad_filter=True)
        result = [TranscriptSegment(start=s.start, end=s.end, text=s.text) for s in segments]
        return result, info.language
