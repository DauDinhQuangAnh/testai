"""Test _clean_text_for_speech - logic thuan, khong can TTS/ffmpeg that."""

from pathlib import Path

import subtitle_pipeline.application.dub as dub
from subtitle_pipeline.application.dub import _clean_text_for_speech
from subtitle_pipeline.domain.models import SubtitleSegment


def test_strips_embedded_newlines_from_line_wrapping():
    text = "day la dong 1\nday la dong 2"

    assert _clean_text_for_speech(text) == "day la dong 1 day la dong 2"


def test_collapses_extra_whitespace():
    text = "  nhieu   khoang trang  \n\n va xuong dong  "

    assert _clean_text_for_speech(text) == "nhieu khoang trang va xuong dong"


def test_empty_or_whitespace_only_becomes_empty_string():
    assert _clean_text_for_speech("   \n  ") == ""


def test_dub_uses_raw_clips_without_stretching(tmp_path, monkeypatch):
    captured = {}

    class FakeTTS:
        sample_rate = 24000

        def __init__(self, language: str):
            self.language = language

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def synthesize(self, text: str, output_path: Path) -> None:
            output_path.write_bytes(b"fake wav")

    def fake_build_dub_track(clips, total_duration, sample_rate, output_path):
        captured["clips"] = clips
        captured["sample_rate"] = sample_rate
        output_path.write_bytes(b"fake track")

    def fake_mux_audio_into_video(video_path, audio_path, output_path):
        output_path.write_bytes(b"fake video")

    monkeypatch.setattr(dub, "EdgeTTSSynthesizer", FakeTTS)
    monkeypatch.setattr(dub, "build_dub_track", fake_build_dub_track)
    monkeypatch.setattr(dub, "mux_audio_into_video", fake_mux_audio_into_video)
    monkeypatch.setattr(dub, "_total_duration", lambda work_dir, source_video: 3.0)
    monkeypatch.setattr(dub.shutil, "rmtree", lambda path, ignore_errors=False: None)

    work_dir = tmp_path / "work"
    out_dir = tmp_path / "out"
    source_video = tmp_path / "input.mp4"
    source_video.write_bytes(b"fake")

    dub.dub_and_export(
        segments=[SubtitleSegment(start=1.0, end=1.5, text="xin\nchao", speaker=None)],
        target_language="vi",
        source_video=source_video,
        work_dir=work_dir,
        out_dir=out_dir,
        stem="input",
    )

    assert captured["sample_rate"] == 24000
    assert captured["clips"] == [(1.0, work_dir / "dub_vi_segments" / "00000_raw.wav")]
    assert not list((work_dir / "dub_vi_segments").glob("*_stretched.wav"))
