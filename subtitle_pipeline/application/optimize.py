"""Toi uu dong subtitle: gioi han so ky tu/dong (CPL - characters per line) va
so dong toi da moi segment, theo quy uoc pho bien trong nganh subtitle (vd.
huong dan cua Netflix duoc dung lam tham chieu). Ham thuan, khong phu thuoc AI
libs nen test duoc ma khong can may dev that.
"""

from subtitle_pipeline.domain.models import SubtitleSegment

DEFAULT_MAX_CHARS_PER_LINE = 42
DEFAULT_MAX_LINES = 2


def optimize_segments(
    segments: list[SubtitleSegment],
    max_chars_per_line: int = DEFAULT_MAX_CHARS_PER_LINE,
    max_lines: int = DEFAULT_MAX_LINES,
) -> list[SubtitleSegment]:
    return [
        SubtitleSegment(
            start=seg.start,
            end=seg.end,
            text=_wrap_text(seg.text, max_chars_per_line, max_lines),
            speaker=seg.speaker,
        )
        for seg in segments
    ]


def _wrap_text(text: str, max_chars_per_line: int, max_lines: int) -> str:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars_per_line or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)

    if len(lines) <= max_lines:
        return "\n".join(lines)

    # Uu tien khong mat noi dung hon la giu dung gioi han ky tu tuyet doi: don
    # het phan du vao dong cuoi cung thay vi cat bo (dong cuoi co the vuot
    # max_chars_per_line).
    kept_lines = lines[: max_lines - 1]
    kept_lines.append(" ".join(lines[max_lines - 1 :]))
    return "\n".join(kept_lines)
