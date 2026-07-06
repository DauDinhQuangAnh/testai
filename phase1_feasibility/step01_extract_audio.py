"""Buoc 1: FFmpeg tach audio tu video mau, chuan hoa ve 16kHz mono PCM.

Goi truc tiep ham `extract_audio` dung trong subtitle_pipeline (Phase 2) thay vi
tu viet lai logic FFmpeg rieng - nho vay so lieu do duoc chinh la hieu nang cua
code se chay that trong production, khong phai mot ban sao co the lech nhau.

Chay: python phase1_feasibility/step01_extract_audio.py samples/<file> --out results/audio_16k.wav
"""

import argparse
import sys
from pathlib import Path

for _parent in Path(__file__).resolve().parents:
    if (_parent / "pyproject.toml").exists():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from measure import measure

from subtitle_pipeline.infrastructure.audio import extract_audio

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Duong dan video/audio mau")
    parser.add_argument("--out", default="results/audio_16k.wav")
    args = parser.parse_args()

    with measure("step01_extract_audio", {"input": args.input}):
        extract_audio(Path(args.input), Path(args.out))
    print(f"Audio saved to {args.out}")
