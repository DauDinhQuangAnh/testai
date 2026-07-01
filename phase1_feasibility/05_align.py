"""Buoc 5: Can chinh thoi gian tung tu bang WhisperX, dua tren transcript o buoc 4.

Chay: python phase1_feasibility/05_align.py results/audio_denoised.wav --transcript results/transcript_medium.json --language vi
"""
import argparse
import json
from pathlib import Path

import whisperx

from utils.measure import measure


def align(input_path: str, transcript_path: str, language: str, device: str):
    with open(transcript_path, encoding="utf-8") as f:
        segments = json.load(f)

    model_a, metadata = whisperx.load_align_model(language_code=language, device=device)
    return whisperx.align(segments, model_a, metadata, input_path, device)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="File audio 16kHz (wav)")
    parser.add_argument("--transcript", required=True, help="JSON tu buoc 04_transcribe")
    parser.add_argument("--language", default="vi")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--out", default="results/aligned.json")
    args = parser.parse_args()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    result = None
    with measure("05_align_whisperx", {"language": args.language}):
        result = align(args.input, args.transcript, args.language, args.device)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Aligned segments -> {args.out}")
