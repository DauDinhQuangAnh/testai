"""Buoc 4: Nhan dang giong noi bang Faster-Whisper.

Cho phep test nhieu model size / compute type khac nhau de so sanh VRAM & thoi gian
(vi du: medium vs large-v3 int8_float16) - day chinh la muc dich cua feasibility spike.

Chay:
  python phase1_feasibility/04_transcribe.py results/audio_denoised.wav --model medium
  python phase1_feasibility/04_transcribe.py results/audio_denoised.wav --model large-v3 --compute-type int8_float16
"""
import argparse
import json
from pathlib import Path

from faster_whisper import WhisperModel

from utils.measure import measure


def transcribe(input_path: str, model_size: str, compute_type: str, device: str):
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, info = model.transcribe(input_path, beam_size=5)
    return list(segments), info


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--model", default="medium", help="medium | large-v3 | large-v3-turbo")
    parser.add_argument("--compute-type", default="int8_float16", help="int8_float16 | int8 | float16")
    parser.add_argument("--device", default="cuda", help="cuda | cpu")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    out_path = args.out or f"results/transcript_{args.model}.json"
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    output_segments = []
    with measure(f"04_transcribe_{args.model}_{args.compute_type}", {
        "model": args.model, "compute_type": args.compute_type, "device": args.device,
    }):
        segs, _info = transcribe(args.input, args.model, args.compute_type, args.device)
        output_segments = [{"start": s.start, "end": s.end, "text": s.text} for s in segs]

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_segments, f, ensure_ascii=False, indent=2)
    print(f"Transcribed {len(output_segments)} segments -> {out_path}")
