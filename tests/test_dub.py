"""Test _clean_text_for_speech - logic thuan, khong can TTS/ffmpeg that."""

from subtitle_pipeline.application.dub import _clean_text_for_speech


def test_strips_embedded_newlines_from_line_wrapping():
    text = "day la dong 1\nday la dong 2"

    assert _clean_text_for_speech(text) == "day la dong 1 day la dong 2"


def test_collapses_extra_whitespace():
    text = "  nhieu   khoang trang  \n\n va xuong dong  "

    assert _clean_text_for_speech(text) == "nhieu khoang trang va xuong dong"


def test_empty_or_whitespace_only_becomes_empty_string():
    assert _clean_text_for_speech("   \n  ") == ""
