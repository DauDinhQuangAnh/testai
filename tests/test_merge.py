"""Test logic gan speaker theo overlap lon nhat (application/merge.py)."""
from subtitle_pipeline.application.merge import merge_speakers
from subtitle_pipeline.domain.models import SpeakerTurn, SubtitleSegment


def test_merge_assigns_dominant_overlapping_speaker():
    segments = [SubtitleSegment(start=0.0, end=2.0, text="hello")]
    turns = [
        SpeakerTurn(start=0.0, end=1.0, speaker="A"),
        SpeakerTurn(start=1.0, end=2.5, speaker="B"),
    ]

    result = merge_speakers(segments, turns)

    assert result[0].speaker == "B"


def test_merge_returns_none_speaker_when_no_overlap():
    segments = [SubtitleSegment(start=10.0, end=12.0, text="hello")]
    turns = [SpeakerTurn(start=0.0, end=1.0, speaker="A")]

    result = merge_speakers(segments, turns)

    assert result[0].speaker is None
