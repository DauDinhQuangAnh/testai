"""Ham export subtitle sang SRT/VTT/ASS/TXT/JSON - ham thuan, khong phu thuoc AI
libs nen test duoc ma khong can may dev that (xem tests/test_export_formats.py).
"""

import json

from subtitle_pipeline.domain.models import SubtitleSegment


def _format_srt_timestamp(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    hours, total_ms = divmod(total_ms, 3_600_000)
    minutes, total_ms = divmod(total_ms, 60_000)
    secs, ms = divmod(total_ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def _format_vtt_timestamp(seconds: float) -> str:
    return _format_srt_timestamp(seconds).replace(",", ".")


def _format_ass_timestamp(seconds: float) -> str:
    total_cs = int(round(seconds * 100))
    hours, total_cs = divmod(total_cs, 360_000)
    minutes, total_cs = divmod(total_cs, 6_000)
    secs, cs = divmod(total_cs, 100)
    return f"{hours:d}:{minutes:02d}:{secs:02d}.{cs:02d}"


def _label(segment: SubtitleSegment) -> str:
    prefix = f"[{segment.speaker}] " if segment.speaker else ""
    return f"{prefix}{segment.text.strip()}"


def _single_line_text(text: str) -> str:
    return " ".join(text.split())


def to_srt(segments: list[SubtitleSegment]) -> str:
    lines = []
    for i, seg in enumerate(segments, start=1):
        lines.append(str(i))
        lines.append(f"{_format_srt_timestamp(seg.start)} --> {_format_srt_timestamp(seg.end)}")
        lines.append(_label(seg))
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def to_vtt(segments: list[SubtitleSegment]) -> str:
    lines = ["WEBVTT", ""]
    for seg in segments:
        lines.append(f"{_format_vtt_timestamp(seg.start)} --> {_format_vtt_timestamp(seg.end)}")
        lines.append(_label(seg))
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def to_ass(segments: list[SubtitleSegment]) -> str:
    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1920\n"
        "PlayResY: 1080\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
        "0,0,0,0,100,100,0,0,1,2,0,2,10,10,20,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Text"
    )
    lines = [header]
    for seg in segments:
        start = _format_ass_timestamp(seg.start)
        end = _format_ass_timestamp(seg.end)
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{_label(seg)}")
    return "\n".join(lines) + "\n"


def to_txt(segments: list[SubtitleSegment]) -> str:
    return "\n".join(_label(seg) for seg in segments) + "\n"


def to_json(segments: list[SubtitleSegment]) -> str:
    data = [
        {
            "start": seg.start,
            "end": seg.end,
            "text": _single_line_text(seg.text),
            "speaker": seg.speaker,
        }
        for seg in segments
    ]
    return json.dumps(data, ensure_ascii=False, indent=2)


FORMAT_WRITERS = {
    "srt": to_srt,
    "vtt": to_vtt,
    "ass": to_ass,
    "txt": to_txt,
    "json": to_json,
}
