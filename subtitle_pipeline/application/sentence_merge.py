"""Gop cac subtitle segment lien tiep (thuong la manh cau do WhisperX chia o
muc tu/cum tu, xem infrastructure/aligner_whisperx.py) thanh 1 segment/cau
hoan chinh dua vao dau cau ket thuc. Dung TRUOC khi dich
(application/translate.py) de NLLB co du ngu canh ca cau, dich tu nhien hon
han so voi dich tung manh roi rac (xem HANDOFF.md).
"""

from subtitle_pipeline.domain.models import SubtitleSegment

SENTENCE_TERMINATORS = (".", "!", "?", "…")


def merge_into_sentences(segments: list[SubtitleSegment]) -> list[SubtitleSegment]:
    merged: list[SubtitleSegment] = []
    buffer: list[SubtitleSegment] = []

    def flush() -> None:
        if not buffer:
            return
        merged.append(
            SubtitleSegment(
                start=buffer[0].start,
                end=buffer[-1].end,
                text=" ".join(seg.text.strip() for seg in buffer),
                speaker=buffer[0].speaker,
            )
        )
        buffer.clear()

    for seg in segments:
        buffer.append(seg)
        if seg.text.strip().endswith(SENTENCE_TERMINATORS):
            flush()
    flush()  # doan cuoi co the khong co dau cau ket thuc - van giu, khong bo

    return merged
