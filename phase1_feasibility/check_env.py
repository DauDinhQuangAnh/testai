"""Kiem tra moi truong truoc khi chay feasibility spike.

Chay: python phase1_feasibility/check_env.py
"""

import os
import shutil
import subprocess
import sys

from dotenv import load_dotenv

load_dotenv()


def check_python():
    print(f"Python: {sys.version}")


def check_ffmpeg():
    path = shutil.which("ffmpeg")
    if not path:
        print("[MISSING] ffmpeg khong co trong PATH. Cai: winget install Gyan.FFmpeg")
        return False
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
    print(f"[OK] ffmpeg: {path}")
    print(f"  {result.stdout.splitlines()[0]}")
    return True


def check_torch_cuda():
    try:
        import torch
    except ImportError:
        print("[MISSING] torch chua duoc cai. Xem HANDOFF.md muc 5, buoc 5.")
        return False
    print(f"[OK] torch: {torch.__version__}")
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        total_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"[OK] CUDA available: {name}, VRAM total: {total_vram_gb:.1f} GB")
    else:
        print(
            "[WARNING] CUDA khong kha dung. Pipeline se chay CPU (rat cham cho Whisper large-v3)."
        )
    return True


def check_packages():
    packages = [
        "faster_whisper",
        "whisperx",
        "pyannote.audio",
        "df",
        "transformers",
        "edge_tts",
        "soundfile",
    ]
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"[OK] package '{pkg}' da cai")
        except ImportError as exc:
            print(f"[MISSING] package '{pkg}': {exc}")


def check_hf_token():
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("[MISSING] Bien moi truong HF_TOKEN chua duoc set (can cho pyannote diarization).")
    else:
        print("[OK] HF_TOKEN da duoc set")


if __name__ == "__main__":
    check_python()
    check_ffmpeg()
    check_torch_cuda()
    check_packages()
    check_hf_token()
