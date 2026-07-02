"""Test merge_into_sentences - logic thuan, khong can AI deps."""

from subtitle_pipeline.application.sentence_merge import merge_into_sentences
from subtitle_pipeline.domain.models import SubtitleSegment


def test_merges_fragments_until_terminal_punctuation():
    segments = [
        SubtitleSegment(start=0.0, end=1.0, text="This is a"),
        SubtitleSegment(start=1.0, end=2.0, text="complete sentence."),
        SubtitleSegment(start=2.0, end=3.0, text="Second one."),
    ]

    result = merge_into_sentences(segments)

    assert [seg.text for seg in result] == ["This is a complete sentence.", "Second one."]
    assert result[0].start == 0.0
    assert result[0].end == 2.0
    assert result[1].start == 2.0
    assert result[1].end == 3.0


def test_keeps_already_complete_sentence_standalone():
    segments = [SubtitleSegment(start=0.0, end=1.0, text="Xin chao.")]

    result = merge_into_sentences(segments)

    assert len(result) == 1
    assert result[0].text == "Xin chao."


def test_flushes_trailing_fragment_without_terminator():
    segments = [
        SubtitleSegment(start=0.0, end=1.0, text="Complete sentence."),
        SubtitleSegment(start=1.0, end=2.0, text="dangling fragment"),
    ]

    result = merge_into_sentences(segments)

    assert [seg.text for seg in result] == ["Complete sentence.", "dangling fragment"]


def test_preserves_speaker_of_first_segment_in_group():
    segments = [
        SubtitleSegment(start=0.0, end=1.0, text="Hello", speaker="SPEAKER_00"),
        SubtitleSegment(start=1.0, end=2.0, text="world.", speaker="SPEAKER_01"),
    ]

    result = merge_into_sentences(segments)

    assert result[0].speaker == "SPEAKER_00"


def test_empty_segments_returns_empty_list():
    assert merge_into_sentences([]) == []
