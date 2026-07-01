"""Buoc 6: Nhan dien nguoi noi bang pyannote speaker-diarization-3.1.

Can HF_TOKEN (bien moi truong hoac file .env) va da accept license cua
pyannote/speaker-diarization-3.1 + pyannote/segmentation-3.0 tren HuggingFace.

Chay: python phase1_feasibility/06_diarize.py results/audio_denoised.wav
"""
import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from pyannote.audio import Pipeline

from utils.measure import measure

load_dotenv()


def diarize(input_path: str, hf_token: str, device: str):
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1", use_auth_token=hf_token
    )
    if device == "cuda":
        import torch
        pipeline.to(torch.device("cuda"))
    diarization = pipeline(input_path)
    return [
        {"start": turn.start, "end": turn.end, "speaker": speaker}
        for turn, _, speaker in diarization.itertracks(yield_label=True)
    ]


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
    turns = None
    with measure("06_diarize_pyannote", {"device": args.device}):
        turns = diarize(args.input, hf_token, args.device)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(turns, f, ensure_ascii=False, indent=2)
    print(f"Found {len(turns)} speaker turns -> {args.out}")
