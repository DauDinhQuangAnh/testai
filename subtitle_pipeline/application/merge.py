"""Gan speaker cho tung subtitle segment dua tren khoang giao (overlap) lon nhat
voi cac luot noi (speaker turn) tu diarization."""
from subtitle_pipeline.domain.models import SpeakerTurn, SubtitleSegment


def merge_speakers(
    segments: list[SubtitleSegment], speaker_turns: list[SpeakerTurn]
) -> list[SubtitleSegment]:
    return [
        SubtitleSegment(
            start=seg.start,
            end=seg.end,
            text=seg.text,
            speaker=_dominant_speaker(seg, speaker_turns),
        )
        for seg in segments
    ]


def _dominant_speaker(segment: SubtitleSegment, turns: list[SpeakerTurn]) -> str | None:
    best_overlap = 0.0
    best_speaker = None
    for turn in turns:
        overlap = min(segment.end, turn.end) - max(segment.start, turn.start)
        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = turn.speaker
    return best_speaker
