"""Ham export subtitle sang SRT/VTT/ASS/TXT/JSON - ham thuan, khong phu thuoc AI
libs nen test duoc ma khong can may dev that (xem tests/test_export_formats.py).
"""

import json
from dataclasses import dataclass

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


@dataclass(frozen=True)
class SubtitleStyle:
    """Style hien thi phu de ASS - mac dinh khop CHINH XAC header cu (truoc
    khi parameterize) de khong doi hanh vi cac cho goi to_ass() khong truyen
    style. Dung boi wizard Upload (buoc Phu de) + hardsub (audio_mux.py).

    Vi tri phu de la toa do TU DO (position_x/position_y, % tinh tu goc
    tren-trai khung hinh) thay vi 3 muc co dinh nhu truoc - FE cho keo tha
    truc tiep tren khung xem truoc (xem NewJob.tsx buoc Phu de).
    """

    font: str = "Arial"
    font_size: int = 48
    text_color: str = "#FFFFFF"
    background_color: str = "#000000"
    outline_width: float = 2.0
    position_x: float = 50.0  # % tu trai, 0..100
    position_y: float = 90.0  # % tu tren, 0..100
    opaque_box: bool = False
    background_opacity: float = 0.5  # 0..1, chi dung cho mau nen sau chu


def _hex_to_ass_color(hex_color: str, alpha: float = 0.0) -> str:
    """#RRGGBB -> &HAABBGGRR (ASS dao thu tu kenh mau, alpha 0=duc 255=trong)."""
    value = hex_color.lstrip("#")
    r, g, b = int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)
    a = round(alpha * 255)
    return f"&H{a:02X}{b:02X}{g:02X}{r:02X}"


def to_ass(segments: list[SubtitleSegment], style: SubtitleStyle | None = None) -> str:
    style = style or SubtitleStyle()
    primary = _hex_to_ass_color(style.text_color)
    outline_color = _hex_to_ass_color("#000000")
    back_color = _hex_to_ass_color(style.background_color, alpha=style.background_opacity)
    border_style = 3 if style.opaque_box else 1
    # \an5\pos(x,y) ghi de vi tri tu Style header (Alignment/Margin ben duoi
    # giu nguyen gia tri cu de tuong thich nguoc, khong con anh huong render).
    pos_x = round(style.position_x / 100 * 1920)
    pos_y = round(style.position_y / 100 * 1080)

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
        f"Style: Default,{style.font},{style.font_size},{primary},&H000000FF,"
        f"{outline_color},{back_color},"
        f"0,0,0,0,100,100,0,0,{border_style},{style.outline_width:g},0,"
        f"2,10,10,20,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Text"
    )
    lines = [header]
    for seg in segments:
        start = _format_ass_timestamp(seg.start)
        end = _format_ass_timestamp(seg.end)
        lines.append(
            f"Dialogue: 0,{start},{end},Default,,0,0,0,,"
            f"{{\\an5\\pos({pos_x},{pos_y})}}{_label(seg)}"
        )
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
