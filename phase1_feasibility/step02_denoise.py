"""Buoc 2: Khu on bang DeepFilterNet3.

Goi adapter `DeepFilterNetDenoiser` dung trong subtitle_pipeline (Phase 2) thay
vi goi thang thu vien df - do duoc VRAM/thoi gian tren chinh code production.

Chay: python phase1_feasibility/step02_denoise.py results/audio_16k.wav \
    --out results/audio_denoised.wav
"""
import argparse
import sys
from pathlib import Path

for _parent in Path(__file__).resolve().parents:
    if (_parent / "pyproject.toml").exists():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from subtitle_pipeline.infrastructure.denoiser_deepfilternet import DeepFilterNetDenoiser

from measure import measure

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--out", default="results/audio_denoised.wav")
    args = parser.parse_args()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with measure("step02_denoise_deepfilternet3", {"input": args.input}):
        with DeepFilterNetDenoiser() as denoiser:
            denoiser.denoise(Path(args.input), Path(args.out))
    print(f"Denoised audio saved to {args.out}")
