"""Orchestrator: chay tuan tu cac buoc 01->06 cua feasibility spike.

Moi buoc duoc chay trong 1 SUBPROCESS RIENG (khong phai import chung trong 1
process) de dam bao VRAM duoc he dieu hanh thu hoi that su giua cac buoc, tranh
do sai do CUDA memory fragmentation/caching allocator neu chay chung 1 process.
Neu 1 buoc that bai, script van tiep tuc cac buoc con lai (khong dung ca chuoi)
de van thu thap duoc so lieu cua cac buoc chay duoc.

Chay: python phase1_feasibility/run_all.py samples/<ten_file>
"""
import argparse
import subprocess
import sys
from pathlib import Path

STEPS = [
    ["01_extract_audio.py", "{input}", "--out", "results/audio_16k.wav"],
    ["02_denoise.py", "results/audio_16k.wav", "--out", "results/audio_denoised.wav"],
    ["03_vad.py", "results/audio_denoised.wav", "--out", "results/vad_segments.json"],
    ["04_transcribe.py", "results/audio_denoised.wav",
        "--model", "medium", "--out", "results/transcript_medium.json"],
    ["04_transcribe.py", "results/audio_denoised.wav",
        "--model", "large-v3", "--compute-type", "int8_float16",
        "--out", "results/transcript_large-v3.json"],
    ["05_align.py", "results/audio_denoised.wav",
        "--transcript", "results/transcript_medium.json", "--out", "results/aligned.json"],
    ["06_diarize.py", "results/audio_denoised.wav", "--out", "results/diarization.json"],
]


def main(input_path: str):
    base = Path(__file__).resolve().parent
    failures = []
    for step in STEPS:
        script = base / step[0]
        args = [a.format(input=input_path) for a in step[1:]]
        cmd = [sys.executable, str(script), *args]
        print(f"\n=== Running: {' '.join(cmd)} ===")
        result = subprocess.run(cmd, cwd=str(base))
        if result.returncode != 0:
            failures.append(step[0])
            print(f"[FAILED] {step[0]} (exit code {result.returncode}) - tiep tuc buoc tiep theo.")

    print("\n=== Xong. ===")
    if failures:
        print(f"Cac buoc that bai: {failures}")
        print("Xem log o tren de biet chi tiet loi, va ghi lai vao HANDOFF.md muc 8.")
    else:
        print("Tat ca cac buoc chay thanh cong.")
    print("Chay tiep: python phase1_feasibility/summarize_results.py de cap nhat HANDOFF.md")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Duong dan file video/audio mau de test (vd: samples/demo.mp4)")
    args = parser.parse_args()
    main(args.input)
