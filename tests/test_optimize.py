"""Test optimize_segments - logic thuan, khong can AI deps."""
from subtitle_pipeline.application.optimize import optimize_segments
from subtitle_pipeline.domain.models import SubtitleSegment


def test_short_text_stays_on_one_line():
    segments = [SubtitleSegment(start=0.0, end=2.0, text="Xin chao")]

    result = optimize_segments(segments, max_chars_per_line=42, max_lines=2)

    assert result[0].text == "Xin chao"


def test_wraps_long_text_without_losing_words():
    long_text = (
        "day la mot cau rat dai can duoc chia thanh nhieu dong de kiem tra "
        "gioi han ky tu moi dong"
    )
    segments = [SubtitleSegment(start=0.0, end=5.0, text=long_text)]

    result = optimize_segments(segments, max_chars_per_line=20, max_lines=2)
    lines = result[0].text.split("\n")

    assert len(lines) <= 2
    assert " ".join(lines).split() == long_text.split()


def test_preserves_start_end_speaker():
    segments = [SubtitleSegment(start=1.5, end=3.5, text="hello", speaker="SPEAKER_00")]

    result = optimize_segments(segments)

    assert result[0].start == 1.5
    assert result[0].end == 3.5
    assert result[0].speaker == "SPEAKER_00"
