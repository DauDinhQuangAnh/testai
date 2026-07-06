"""Buoc 3: Phat hien giong noi bang Silero VAD.

CHI de do hieu nang tham khao - subtitle_pipeline (Phase 2) khong dung Silero
VAD rieng, ma dung `vad_filter=True` tich hop san trong Faster-Whisper (xem
HANDOFF.md muc "Quyet dinh moi"), nen khong co adapter tuong duong de tai su
dung o day.

Chay: python phase1_feasibility/step03_vad.py results/audio_denoised.wav \
    --out results/vad_segments.json
"""

import argparse
import json
from pathlib import Path

import torch
from measure import measure


def run_vad(input_path: str):
    model, utils = torch.hub.load(
        repo_or_dir="snakers4/silero-vad", model="silero_vad", trust_repo=True
    )
    get_speech_timestamps, _, read_audio, *_ = utils
    wav = read_audio(input_path, sampling_rate=16000)
    return get_speech_timestamps(wav, model, sampling_rate=16000)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--out", default="results/vad_segments.json")
    args = parser.parse_args()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    segments = []
    with measure("step03_vad_silero", {"input": args.input}):
        segments = run_vad(args.input)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=2)
    print(f"Found {len(segments)} speech segments, saved to {args.out}")
