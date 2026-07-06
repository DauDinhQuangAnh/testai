"""Buoc 6: Nhan dien nguoi noi bang pyannote speaker-diarization-3.1.

Goi adapter `PyannoteDiarizer` dung trong subtitle_pipeline (Phase 2). Can
HF_TOKEN (bien moi truong hoac file .env) va da accept license cua
pyannote/speaker-diarization-3.1 + pyannote/segmentation-3.0 tren HuggingFace.

Chay: python phase1_feasibility/step06_diarize.py results/audio_denoised.wav
"""

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

from dotenv import load_dotenv

for _parent in Path(__file__).resolve().parents:
    if (_parent / "pyproject.toml").exists():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from measure import measure

from subtitle_pipeline.infrastructure.diarizer_pyannote import PyannoteDiarizer

load_dotenv()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--out", default="results/diarization.json")
    args = parser.parse_args()

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        raise SystemExit("HF_TOKEN chua duoc set. Xem HANDOFF.md muc 5, buoc 7.")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    turns = []
    with (
        measure("step06_diarize_pyannote", {"device": args.device}),
        PyannoteDiarizer(hf_token, args.device) as diarizer,
    ):
        turns = diarizer.diarize(Path(args.input))

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump([asdict(t) for t in turns], f, ensure_ascii=False, indent=2)
    print(f"Found {len(turns)} speaker turns -> {args.out}")
