"""Buoc 5: Can chinh thoi gian tung tu bang WhisperX, dua tren transcript o buoc 4.

Goi adapter `WhisperXAligner` dung trong subtitle_pipeline (Phase 2).

Chay: python phase1_feasibility/step05_align.py results/audio_denoised.wav \
    --transcript results/transcript_medium.json --language vi
"""
import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

for _parent in Path(__file__).resolve().parents:
    if (_parent / "pyproject.toml").exists():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from subtitle_pipeline.domain.models import TranscriptSegment
from subtitle_pipeline.infrastructure.aligner_whisperx import WhisperXAligner

from measure import measure

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="File audio 16kHz (wav)")
    parser.add_argument("--transcript", required=True, help="JSON tu buoc step04_transcribe")
    parser.add_argument("--language", default="vi")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--out", default="results/aligned.json")
    args = parser.parse_args()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.transcript, encoding="utf-8") as f:
        transcript = [TranscriptSegment(**seg) for seg in json.load(f)]

    aligned = []
    with measure("step05_align_whisperx", {"language": args.language}):
        with WhisperXAligner(args.language, args.device) as aligner:
            aligned = aligner.align(Path(args.input), transcript)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump([asdict(seg) for seg in aligned], f, ensure_ascii=False, indent=2)
    print(f"Aligned segments -> {args.out}")
