"""Buoc 1: FFmpeg tach audio tu video mau, chuan hoa ve 16kHz mono PCM.

Chay: python phase1_feasibility/01_extract_audio.py samples/<file> --out results/audio_16k.wav
"""
import argparse
import subprocess
from pathlib import Path

from utils.measure import measure


def extract_audio(input_path: str, output_path: str, sample_rate: int = 16000):
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vn", "-ac", "1", "-ar", str(sample_rate),
        "-c:a", "pcm_s16le",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Duong dan video/audio mau")
    parser.add_argument("--out", default="results/audio_16k.wav")
    args = parser.parse_args()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with measure("01_extract_audio", {"input": args.input}):
        extract_audio(args.input, args.out)
    print(f"Audio saved to {args.out}")
