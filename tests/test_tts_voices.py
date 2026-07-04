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


def test_voice_catalog_marks_native_voices_recommended_first():
    from subtitle_pipeline.infrastructure.tts_edge import voice_catalog

    catalog = voice_catalog("vi")

    assert catalog[0]["recommended"] is True
    assert catalog[0]["id"].startswith("vi-VN")
    # Multilingual (khong phai ban dia) khong duoc danh dau recommended.
    multilingual = [v for v in catalog if "Multilingual" in v["id"]]
    assert multilingual and all(not v["recommended"] for v in multilingual)


def test_voice_catalog_has_gender_and_style():
    from subtitle_pipeline.infrastructure.tts_edge import voice_catalog

    for entry in voice_catalog("vi"):
        assert entry["gender"] in ("nam", "nữ")
        assert entry["style"]


def test_synthesizer_formats_rate_and_pitch_with_sign():
    tts = EdgeTTSSynthesizer("vi", rate_percent=25, pitch_hz=-5)

    assert tts._rate == "+25%"
    assert tts._pitch == "-5Hz"


def test_synthesizer_defaults_to_neutral_rate_pitch():
    tts = EdgeTTSSynthesizer("vi")

    assert tts._rate == "+0%"
    assert tts._pitch == "+0Hz"
