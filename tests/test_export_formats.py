"""Test cac ham export - thuan, khong AI deps, chay duoc ngay ca khong co GPU/model."""

import json

from subtitle_pipeline.domain.models import SubtitleSegment
from subtitle_pipeline.export.formats import to_ass, to_json, to_srt, to_txt, to_vtt

SEGMENTS = [
    SubtitleSegment(start=0.0, end=1.5, text="Xin chao", speaker="SPEAKER_00"),
    SubtitleSegment(start=1.5, end=3.25, text="The gioi", speaker=None),
]


def test_to_srt_format():
    output = to_srt(SEGMENTS)
    assert "00:00:00,000 --> 00:00:01,500" in output
    assert "[SPEAKER_00] Xin chao" in output
    assert "The gioi" in output


def test_to_vtt_format():
    output = to_vtt(SEGMENTS)
    assert output.startswith("WEBVTT")
    assert "00:00:00.000 --> 00:00:01.500" in output


def test_to_json_roundtrip():
    data = json.loads(to_json(SEGMENTS))
    assert data[0]["speaker"] == "SPEAKER_00"
    assert data[1]["speaker"] is None


def test_to_json_removes_line_wrapping_newlines():
    segments = [
        SubtitleSegment(
            start=0.0,
            end=1.0,
            text="SQL for\nshort,\n\n  keeps going",
            speaker=None,
        )
    ]

    data = json.loads(to_json(segments))

    assert data[0]["text"] == "SQL for short, keeps going"


def test_to_txt_contains_all_lines():
    output = to_txt(SEGMENTS)
    assert "Xin chao" in output
    assert "The gioi" in output


def test_to_ass_contains_dialogue_lines():
    output = to_ass(SEGMENTS)
    assert "Dialogue: 0,0:00:00.00,0:00:01.50,Default" in output
