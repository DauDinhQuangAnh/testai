"""Buoc 4: Nhan dang giong noi bang Faster-Whisper.

Goi adapter `FasterWhisperTranscriber` dung trong subtitle_pipeline (Phase 2).
Cho phep doi model size/compute type qua tham so de so sanh VRAM & thoi gian
(vi du: medium vs large-v3 int8_float16) - day chinh la muc dich cua feasibility
spike.

Chay:
  python phase1_feasibility/step04_transcribe.py results/audio_denoised.wav --model medium
  python phase1_feasibility/step04_transcribe.py results/audio_denoised.wav \
      --model large-v3 --compute-type int8_float16
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

from subtitle_pipeline.infrastructure.transcriber_faster_whisper import FasterWhisperTranscriber

from measure import measure

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--model", default="medium", help="medium | large-v3 | large-v3-turbo")
    parser.add_argument(
        "--compute-type", default="int8_float16", help="int8_float16 | int8 | float16"
    )
    parser.add_argument("--device", default="cuda", help="cuda | cpu")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    out_path = args.out or f"results/transcript_{args.model}.json"
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    segments = []
    step_name = f"step04_transcribe_{args.model}_{args.compute_type}"
    extra = {"model": args.model, "compute_type": args.compute_type, "device": args.device}
    with measure(step_name, extra):
        with FasterWhisperTranscriber(args.model, args.compute_type, args.device) as transcriber:
            segments = transcriber.transcribe(Path(args.input))

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump([asdict(seg) for seg in segments], f, ensure_ascii=False, indent=2)
    print(f"Transcribed {len(segments)} segments -> {out_path}")
