"""Adapter text-to-speech dung `edge-tts` (goi giong Neural TTS that cua
Microsoft qua tinh nang "Doc to" tren trinh duyet Edge - mien phi, khong can
API key, khong can dang ky tai khoan).

**THAY THE `tts_mms.py` (MMS-TTS) sau khi test tren may dev that (2026-07-03):
chat luong giong doc cua MMS-TTS qua te (VITS robot, phat am sai nhieu) - xem
HANDOFF.md Phase 5b, muc "Quyet dinh moi".** edge-tts cho giong tu nhien hon
han vi day chinh la giong Azure Neural TTS thuong mai cua Microsoft, chi la
duoc expose mien phi qua giao thuc noi bo cua Edge.

**DANH DOI QUAN TRONG:** day la adapter DUY NHAT trong toan bo pipeline can
INTERNET (goi API cua Microsoft qua thu vien `edge-tts`, khong chay local nhu
Whisper/WhisperX/pyannote/DeepFilterNet/NLLB). Vi day la giao thuc noi bo
KHONG chinh thuc (reverse-engineered tu Edge browser, khong phai API chinh
thuc duoc Microsoft cong bo/dam bao), Microsoft co the thay doi va lam gian
doan bat ky luc nao - neu gap loi ket noi, kiem tra phien ban `edge-tts` moi
nhat (`pip install -U edge-tts`) truoc. Neu can bo phu thuoc internet hoan
toan sau nay, xem lai VieNeu-TTS (github.com/pnnbao97/VieNeu-TTS) - TTS tieng
Viet local/GPU, co voice cloning, nhung chua duoc thu nghiem trong du an nay.
"""
import subprocess
from pathlib import Path

# Ma ngon ngu noi bo (giong NLLB_LANGUAGE_CODES) -> ten giong Edge TTS. Chi
# liet ke ngon ngu pipeline nay da ho tro o buoc dich (xem
# translator_nllb.SUPPORTED_LANGUAGES). Voi tieng Viet, HoaiMy va NamMinh la 2
# giong Neural duoc danh gia tot nhat hien co (nu/nam).
EDGE_TTS_VOICES = {
    "vi": "vi-VN-HoaiMyNeural",
    "en": "en-US-AriaNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural",
    "fr": "fr-FR-DeniseNeural",
    "es": "es-ES-ElviraNeural",
}

# Chuan hoa 1 sample rate co dinh cho moi clip xuat ra (ep bang ffmpeg khi
# chuyen mp3 -> wav ben duoi) de build_dub_track khong can doan/resample.
OUTPUT_SAMPLE_RATE = 24000


class EdgeTTSSynthesizer:
    def __init__(self, language: str):
        if language not in EDGE_TTS_VOICES:
            raise ValueError(f"Ngon ngu TTS chua ho tro: {language}")
        self._voice = EDGE_TTS_VOICES[language]

    def __enter__(self) -> "EdgeTTSSynthesizer":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    @property
    def sample_rate(self) -> int:
        return OUTPUT_SAMPLE_RATE

    def synthesize(self, text: str, output_path: Path) -> None:
        import asyncio

        import edge_tts

        output_path.parent.mkdir(parents=True, exist_ok=True)
        mp3_path = output_path.with_suffix(".mp3")

        communicate = edge_tts.Communicate(text, self._voice)
        asyncio.run(communicate.save(str(mp3_path)))

        # Chuyen mp3 (dinh dang edge-tts tra ve) sang wav PCM chuan, ep sample
        # rate co dinh - de tuong thich voi audio_timing.py/audio_mux.py, cung
        # dinh dang voi ket qua cac adapter TTS local khac neu doi lai sau nay.
        cmd = [
            "ffmpeg", "-y", "-i", str(mp3_path),
            "-ar", str(OUTPUT_SAMPLE_RATE), "-ac", "1",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        mp3_path.unlink(missing_ok=True)
