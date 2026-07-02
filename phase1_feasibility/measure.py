"""Do thoi gian va VRAM peak cho tung buoc cua feasibility spike.

Moi ket qua duoc ghi (append) vao results/phase1_results.jsonl. Dung
summarize_results.py de tong hop lai thanh bang trong HANDOFF.md.
"""
import json
import time
from contextlib import contextmanager
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_FILE = RESULTS_DIR / "phase1_results.jsonl"


@contextmanager
def measure(step_name: str, extra: dict | None = None):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        import torch
        cuda_available = torch.cuda.is_available()
    except ImportError:
        torch = None
        cuda_available = False

    if cuda_available:
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()

    start = time.perf_counter()
    error = None
    try:
        yield
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        if cuda_available:
            torch.cuda.synchronize()
            vram_peak_mb = torch.cuda.max_memory_allocated() / (1024 ** 2)
        else:
            vram_peak_mb = None
        elapsed = time.perf_counter() - start

        record = {
            "step": step_name,
            "elapsed_sec": round(elapsed, 2),
            "vram_peak_mb": round(vram_peak_mb, 1) if vram_peak_mb is not None else None,
            "error": error,
            "extra": extra or {},
        }
        with open(RESULTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        status = "FAILED" if error else "OK"
        vram_msg = f", VRAM peak {vram_peak_mb:.0f} MB" if vram_peak_mb is not None else ""
        error_msg = f" | ERROR: {error}" if error else ""
        print(f"[{status}] {step_name}: {elapsed:.2f}s{vram_msg}{error_msg}")
