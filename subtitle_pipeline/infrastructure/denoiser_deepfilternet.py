"""Adapter cho DeepFilterNet3. Import thu vien AI (df) chi trong __enter__, khong
o top-level module - nho vay cac module khac (application/, export/, domain/) va
test cua chung khong bi buoc phai cai deepfilternet.
"""
from pathlib import Path

from subtitle_pipeline.infrastructure.gpu import release_gpu_memory


class DeepFilterNetDenoiser:
    def __init__(self):
        self._model = None
        self._df_state = None

    def __enter__(self) -> "DeepFilterNetDenoiser":
        from df.enhance import init_df
        self._model, self._df_state, _ = init_df()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._model = None
        self._df_state = None
        release_gpu_memory()

    def denoise(self, input_path: Path, output_path: Path) -> None:
        from df.enhance import enhance, load_audio, save_audio
        output_path.parent.mkdir(parents=True, exist_ok=True)
        audio, _ = load_audio(str(input_path), sr=self._df_state.sr())
        enhanced = enhance(self._model, self._df_state, audio)
        save_audio(str(output_path), enhanced, self._df_state.sr())
