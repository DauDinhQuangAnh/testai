"""Adapter text-to-speech DUNG DE CLONE GIONG (VieNeu-TTS,
github.com/pnnbao97/VieNeu-TTS) - khac han `tts_edge.py` (giong co san, khong
clone). Nguoi dung doc 1 doan mau (~vai chuc giay), he thong dung doan do lam
"reference audio" de sinh giong noi CUNG timbre cho toan bo cau thoai long
tieng - xem `application/dub.py` (`DubRenderOptions.custom_voice_ref_audio`).

**Da SPIKE THAT truoc khi viet adapter nay (2026-07-14, xem HANDOFF.md muc
6p)** - khong phai code chua tung chay thu nhu da so adapter khac trong du
an: cai `vieneu`, tai model that tu HuggingFace, dung edge-tts sinh 1 clip
tieng Viet lam reference, goi `infer()` va xac nhan audio dau ra hop le
(khong rong/khong loi). 2 diem phai xu ly de chay duoc, da gap chinh trong
spike:
- Model cong khai tren HuggingFace nhung tai qua co che "Xet" tang toc co
  the loi 401 (khong xac thuc) trong mot so moi truong mang - dat
  `HF_HUB_DISABLE_XET=1` LAM MAC DINH (khong ghi de neu nguoi dung da tu dat)
  de fallback ve tai HTTP thuong.
- Du tai lieu ghi "CPU torch-free", buoc trich xuat speaker embedding (thu
  vien noi bo `vieneu`) VAN can `torchaudio` (khong chi `torch`) - can cai
  them `torchaudio` cung luc voi `torch` (xem huong dan `requirements.txt`).

**Danh doi:** VieNeu-TTS la du an ca nhan (1 tac gia), it duoc kiem chung
hon Coqui/MyShell - chat luong giong clone tieng Viet CHUA duoc nguoi dung
tu nghe danh gia (spike chi xac nhan pipeline chay duoc, khong danh gia
duoc chat luong qua tai). Tren CPU (sandbox viet code nay), sinh 1 cau ngan
mat ~30s (~8x cham hon thoi gian thuc) - qua cham de dung that; tren GPU
CUDA that (RTX 4050), thu vien tu chuyen sang backend PyTorch nhanh hon
nhieu (`device="auto"` trong `Vieneu()` tu nhan dien CUDA) nhung CHUA duoc
do toc do thuc te tren GPU that.
"""

import os
import subprocess
from pathlib import Path

# Xem docstring o tren - tranh loi 401 khi tai model qua "Xet" trong 1 so
# moi truong mang. Chi dat neu nguoi dung/moi truong chua tu cau hinh.
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

# Cung 1 sample rate voi tts_edge.py (OUTPUT_SAMPLE_RATE) de build_dub_track
# khong can phan biet clip nao sinh boi synthesizer nao.
OUTPUT_SAMPLE_RATE = 24000

MIN_REFERENCE_SECONDS = 3.0


class VieNeuCloneSynthesizer:
    """1 doi tuong = 1 giong da clone (1 file reference audio). Model
    v3-turbo (~vai tram MB, tai tu HuggingFace lan dau) + buoc "enroll" giong
    (trich speaker embedding tu reference audio) deu CHI chay 1 LAN o
    `__enter__` roi tai su dung cho moi cau trong `synthesize()` - tranh
    tai lai model/ma hoa lai reference cho tung segment phu de.
    """

    def __init__(self, ref_audio_path: Path):
        self._ref_audio_path = ref_audio_path
        self._tts = None
        self._voice_ref: dict | None = None

    def __enter__(self) -> "VieNeuCloneSynthesizer":
        from vieneu import Vieneu

        self._tts = Vieneu(mode="v3turbo")
        speaker_emb, ref_codes = self._tts.encode_reference(str(self._ref_audio_path), denoise=True)
        self._voice_ref = {"speaker_emb": speaker_emb, "codes": ref_codes}
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._tts is not None:
            self._tts.close()
        self._tts = None
        self._voice_ref = None
        return None

    def synthesize(self, text: str, output_path: Path) -> None:
        wav = self._tts.infer(text, voice=self._voice_ref)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path = output_path.with_suffix(".raw.wav")
        import soundfile as sf

        sf.write(str(raw_path), wav, self._tts.sample_rate)

        # Ep ve cung sample rate/mono voi tts_edge.py (xem OUTPUT_SAMPLE_RATE)
        # - dong nhat dinh dang du clip sinh boi synthesizer nao.
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(raw_path),
            "-ar",
            str(OUTPUT_SAMPLE_RATE),
            "-ac",
            "1",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        raw_path.unlink(missing_ok=True)


def probe_reference_seconds(ref_audio_path: Path) -> float:
    """Do do dai (giay) 1 file audio mau - dung de canh bao nguoi dung o UI
    neu doan doc qua ngan (VieNeu-TTS can toi thieu vai giay de clone)."""
    import soundfile as sf

    info = sf.info(str(ref_audio_path))
    return info.frames / info.samplerate
