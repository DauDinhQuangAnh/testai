"""Giai phong VRAM giua cac buoc pipeline. May dev VRAM han che (6GB - xem
docs/memory/dev-machine-rtx4050.md) khong the giu nhieu model GPU resident cung
luc, nen moi adapter goi ham nay trong __exit__ sau khi model bi xoa tham chieu.

LUU Y: giai phong trong CUNG 1 process (gc.collect + torch.cuda.empty_cache) it
dam bao hon cach do bang subprocess rieng cua Phase 1 feasibility spike. Chua
duoc xac minh thuc te tren may dev (xem HANDOFF.md muc "Van de dang mo").
"""
import gc


def release_gpu_memory() -> None:
    gc.collect()
    try:
        import torch
    except ImportError:
        return
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
