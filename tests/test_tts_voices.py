"""Test danh sach giong doc (VOICE_OPTIONS) - khong goi mang/edge-tts that,
chi kiem tra tinh nhat quan cua bang cau hinh giong.
"""

import pytest

from subtitle_pipeline.infrastructure.translator_nllb import SUPPORTED_LANGUAGES
from subtitle_pipeline.infrastructure.tts_edge import (
    VOICE_OPTIONS,
    EdgeTTSSynthesizer,
    default_voice,
)


def test_voice_options_cover_all_supported_languages():
    assert set(VOICE_OPTIONS.keys()) == set(SUPPORTED_LANGUAGES)


def test_every_language_has_multiple_voices():
    for language, voices in VOICE_OPTIONS.items():
        assert len(voices) >= 2, f"Ngon ngu '{language}' chi co {len(voices)} giong"


def test_vietnamese_has_both_native_voices():
    vi_voices = set(VOICE_OPTIONS["vi"].values())

    assert "vi-VN-HoaiMyNeural" in vi_voices
    assert "vi-VN-NamMinhNeural" in vi_voices


def test_default_voice_is_first_option():
    assert default_voice("vi") == "vi-VN-HoaiMyNeural"


def test_default_voice_unknown_language_raises():
    with pytest.raises(ValueError):
        default_voice("xx")


def test_synthesizer_uses_default_when_voice_not_given():
    tts = EdgeTTSSynthesizer("vi")

    assert tts._voice == "vi-VN-HoaiMyNeural"


def test_synthesizer_accepts_explicit_voice():
    tts = EdgeTTSSynthesizer("vi", voice="vi-VN-NamMinhNeural")

    assert tts._voice == "vi-VN-NamMinhNeural"