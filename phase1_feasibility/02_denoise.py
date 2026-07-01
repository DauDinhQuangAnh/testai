"""Buoc 2: Khu on bang DeepFilterNet3.

Chay: python phase1_feasibility/02_denoise.py results/audio_16k.wav --out results/audio_denoised.wav
"""
import argparse
from pathlib import Path

from df.enhance import enhance, init_df, load_audio, save_audio

from utils.measure import measure


def denoise(input_path: str, output_path: str):
    model, df_state, _ = init_df()
    audio, _ = load_audio(input_path, sr=df_state.sr())
    enhanced = enhance(model, df_state, audio)
    save_audio(output_path, enhanced, df_state.sr())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--out", default="results/audio_denoised.wav")
    args = parser.parse_args()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with measure("02_denoise_deepfilternet3", {"input": args.input}):
        denoise(args.input, args.out)
    print(f"Denoised audio saved to {args.out}")
