"""Test cac ham export - thuan, khong AI deps, chay duoc ngay ca khong co GPU/model."""

import json

from subtitle_pipeline.domain.models import SubtitleSegment
from subtitle_pipeline.export.formats import SubtitleStyle, to_ass, to_json, to_srt, to_txt, to_vtt

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


def test_to_ass_default_style_matches_legacy_header():
    output = to_ass(SEGMENTS)

    assert (
        "Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
        "0,0,0,0,100,100,0,0,1,2,0,2,10,10,20,1"
    ) in output


def test_to_ass_custom_style_changes_alignment_box_and_colors():
    style = SubtitleStyle(
        font="Tahoma",
        font_size=60,
        text_color="#FFFF00",
        position="top",
        opaque_box=True,
        outline_width=3.0,
    )

    output = to_ass(SEGMENTS, style)

    style_line = next(line for line in output.splitlines() if line.startswith("Style:"))
    fields = style_line.removeprefix("Style: ").split(",")
    assert fields[1] == "Tahoma"
    assert fields[2] == "60"
    assert fields[3] == "&H0000FFFF"  # vang: ASS dao BGR nen FFFF00 -> 00FFFF
    assert fields[15] == "3"  # BorderStyle 3 = hop nen dac
    assert fields[16] == "3"  # do day vien
    assert fields[18] == "8"  # Alignment 8 = tren
