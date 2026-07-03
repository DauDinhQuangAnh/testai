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

# Cac giong "Multilingual" cua Azure Neural TTS - 1 giong doc duoc RAT NHIEU
# ngon ngu (bao gom tieng Viet), tu nhan dien ngon ngu tu text dau vao. Da
# xac nhan co mat trong danh sach cua edge-tts (endpoint mien phi). Dung lam
# lua chon bo sung cho MOI ngon ngu ben canh giong ban dia.
_MULTILINGUAL_VOICES = {
    "Ava (nữ, đa ngôn ngữ)": "en-US-AvaMultilingualNeural",
    "Emma (nữ, đa ngôn ngữ)": "en-US-EmmaMultilingualNeural",
    "Seraphina (nữ, đa ngôn ngữ)": "de-DE-SeraphinaMultilingualNeural",
    "Vivienne (nữ, đa ngôn ngữ)": "fr-FR-VivienneMultilingualNeural",
    "Xiaoxiao ĐNN (nữ, đa ngôn ngữ)": "zh-CN-XiaoxiaoMultilingualNeural",
    "Andrew (nam, đa ngôn ngữ)": "en-US-AndrewMultilingualNeural",
    "Brian (nam, đa ngôn ngữ)": "en-US-BrianMultilingualNeural",
    "Remy (nam, đa ngôn ngữ)": "fr-FR-RemyMultilingualNeural",
    "Florian (nam, đa ngôn ngữ)": "de-DE-FlorianMultilingualNeural",
}

# Ma ngon ngu noi bo (khop translator_nllb.SUPPORTED_LANGUAGES) -> danh sach
# giong cho nguoi dung chon: {nhan hien thi: ten giong Edge TTS}. Giong DAU
# TIEN trong moi dict la mac dinh (dict Python giu thu tu chen). Moi ngon ngu
# gom giong ban dia (nam/nu) + cac giong multilingual dung chung o tren.
# Tieng Viet: HoaiMy/NamMinh la 2 giong thuan Viet duy nhat edge-tts co.
VOICE_OPTIONS: dict[str, dict[str, str]] = {
    "vi": {
        "HoaiMy (nữ, mặc định)": "vi-VN-HoaiMyNeural",
        "NamMinh (nam)": "vi-VN-NamMinhNeural",
        **_MULTILINGUAL_VOICES,
    },
    "en": {
        "Aria (nữ, mặc định)": "en-US-AriaNeural",
        "Guy (nam)": "en-US-GuyNeural",
        "Jenny (nữ)": "en-US-JennyNeural",
        **_MULTILINGUAL_VOICES,
    },
    "zh": {
        "Xiaoxiao (nữ, mặc định)": "zh-CN-XiaoxiaoNeural",
        "Yunxi (nam)": "zh-CN-YunxiNeural",
        **_MULTILINGUAL_VOICES,
    },
    "ja": {
        "Nanami (nữ, mặc định)": "ja-JP-NanamiNeural",
        "Keita (nam)": "ja-JP-KeitaNeural",
        **_MULTILINGUAL_VOICES,
    },
    "ko": {
        "SunHi (nữ, mặc định)": "ko-KR-SunHiNeural",
        "InJoon (nam)": "ko-KR-InJoonNeural",
        **_MULTILINGUAL_VOICES,
    },
    "fr": {
        "Denise (nữ, mặc định)": "fr-FR-DeniseNeural",
        "Henri (nam)": "fr-FR-HenriNeural",
        **_MULTILINGUAL_VOICES,
    },
    "es": {
        "Elvira (nữ, mặc định)": "es-ES-ElviraNeural",
        "Alvaro (nam)": "es-ES-AlvaroNeural",
        **_MULTILINGUAL_VOICES,
    },
}


def default_voice(language: str) -> str:
    if language not in VOICE_OPTIONS:
        raise ValueError(f"Ngôn ngữ TTS chưa hỗ trợ: {language}")
    return next(iter(VOICE_OPTIONS[language].values()))

# Chuan hoa 1 sample rate co dinh cho moi clip xuat ra (ep bang ffmpeg khi
# chuyen mp3 -> wav ben duoi) de build_dub_track khong can doan/resample.
OUTPUT_SAMPLE_RATE = 24000


class EdgeTTSSynthesizer:
    def __init__(self, language: str, voice: str | None = None):
        self._voice = voice or default_voice(language)

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
            "ffmpeg",
            "-y",
            "-i",
            str(mp3_path),
            "-ar",
            str(OUTPUT_SAMPLE_RATE),
            "-ac",
            "1",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        mp3_path.unlink(missing_ok=True)
