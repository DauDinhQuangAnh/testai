"""Test cac ham thuan cua application/dub.py (_clean_text_for_speech,
_build_speaker_voice_map, _fit_target_duration) + flow dub_and_export voi
adapter fake - khong can TTS/ffmpeg that."""

from pathlib import Path

import subtitle_pipeline.application.dub as dub
from subtitle_pipeline.application.dub import (
    MAX_TEMPO_FACTOR,
    DubRenderOptions,
    _build_speaker_voice_map,
    _clean_text_for_speech,
    _fit_target_duration,
)
from subtitle_pipeline.domain.models import SubtitleSegment
from subtitle_pipeline.infrastructure.tts_edge import VOICE_OPTIONS, default_voice


def test_strips_embedded_newlines_from_line_wrapping():
    text = "day la dong 1\nday la dong 2"

    assert _clean_text_for_speech(text) == "day la dong 1 day la dong 2"


def test_collapses_extra_whitespace():
    text = "  nhieu   khoang trang  \n\n va xuong dong  "

    assert _clean_text_for_speech(text) == "nhieu khoang trang va xuong dong"


def test_empty_or_whitespace_only_becomes_empty_string():
    assert _clean_text_for_speech("   \n  ") == ""


def test_speaker_voice_map_single_speaker_uses_given_voice():
    segments = [SubtitleSegment(start=0.0, end=1.0, text="hi", speaker="SPEAKER_00")]

    result = _build_speaker_voice_map(segments, "vi", "vi-VN-NamMinhNeural")

    assert result == {"SPEAKER_00": "vi-VN-NamMinhNeural"}


def test_speaker_voice_map_uses_default_voice_when_none_given():
    segments = [SubtitleSegment(start=0.0, end=1.0, text="hi", speaker=None)]

    result = _build_speaker_voice_map(segments, "vi", None)

    assert result == {None: default_voice("vi")}


def test_speaker_voice_map_assigns_distinct_voice_to_second_speaker():
    segments = [
        SubtitleSegment(start=0.0, end=1.0, text="hi", speaker="SPEAKER_00"),
        SubtitleSegment(start=1.0, end=2.0, text="hello", speaker="SPEAKER_01"),
    ]

    result = _build_speaker_voice_map(segments, "vi", "vi-VN-HoaiMyNeural")

    assert result["SPEAKER_00"] == "vi-VN-HoaiMyNeural"
    assert result["SPEAKER_01"] != "vi-VN-HoaiMyNeural"


def test_speaker_voice_map_reuses_voice_for_repeated_speaker():
    segments = [
        SubtitleSegment(start=0.0, end=1.0, text="hi", speaker="SPEAKER_00"),
        SubtitleSegment(start=1.0, end=2.0, text="hello", speaker="SPEAKER_01"),
        SubtitleSegment(start=2.0, end=3.0, text="again", speaker="SPEAKER_00"),
    ]

    result = _build_speaker_voice_map(segments, "vi", "vi-VN-HoaiMyNeural")

    assert len(result) == 2  # khong tao them entry cho lan SPEAKER_00 xuat hien lai


def test_speaker_voice_map_cycles_when_more_speakers_than_voices():
    total_voices = len(VOICE_OPTIONS["vi"])
    segments = [
        SubtitleSegment(start=float(i), end=float(i + 1), text="x", speaker=f"SPEAKER_{i:02d}")
        for i in range(total_voices + 2)
    ]

    result = _build_speaker_voice_map(segments, "vi", None)

    assert len(result) == total_voices + 2  # van gan du, xoay vong khong loi


def test_fit_target_duration_returns_none_when_clip_fits_window():
    assert _fit_target_duration(clip_duration=2.0, window_seconds=3.0) is None


def test_fit_target_duration_tolerates_small_overflow():
    # Tran 4% < FIT_TOLERANCE 5% - khong dang re-encode.
    assert _fit_target_duration(clip_duration=2.08, window_seconds=2.0) is None


def test_fit_target_duration_shrinks_to_window_when_within_max_tempo():
    assert _fit_target_duration(clip_duration=2.4, window_seconds=2.0) == 2.0


def test_fit_target_duration_caps_speedup_at_max_tempo():
    # Can 2x moi vua window 2.0 - vuot nguong, chi tang toc MAX_TEMPO_FACTOR.
    target = _fit_target_duration(clip_duration=4.0, window_seconds=2.0)

    assert target == 4.0 / MAX_TEMPO_FACTOR
    assert target > 2.0  # van tran, phan du chap nhan chong lan


def test_fit_target_duration_ignores_non_positive_window():
    assert _fit_target_duration(clip_duration=1.0, window_seconds=0.0) is None


def test_dub_speeds_up_clip_longer_than_gap_to_next_segment(tmp_path, monkeypatch):
    captured = {}
    stretch_calls = []

    class FakeTTS:
        def __init__(self, language: str, voice: str | None = None, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def synthesize(self, text: str, output_path: Path) -> None:
            output_path.write_bytes(b"fake wav")

    def fake_stretch(input_path, output_path, target_duration):
        stretch_calls.append((input_path, output_path, target_duration))
        output_path.write_bytes(b"fake fitted wav")

    monkeypatch.setattr(dub, "EdgeTTSSynthesizer", FakeTTS)
    monkeypatch.setattr(dub, "build_dub_track", lambda *a, **k: captured.update(clips=a[0]))
    monkeypatch.setattr(
        dub, "mux_audio_into_video", lambda *a, **k: a[2].write_bytes(b"fake video")
    )
    monkeypatch.setattr(dub, "_total_duration", lambda work_dir, source_video: 10.0)
    # Clip dau dai 2.4s nhung cau ke tiep bat dau sau 2s -> tang toc 1.2x
    # (trong nguong MAX_TEMPO_FACTOR) ve dung 2s.
    monkeypatch.setattr(
        dub, "_clip_duration_seconds", lambda path: 2.4 if "00000" in path.name else 1.0
    )
    monkeypatch.setattr(dub, "time_stretch_to_duration", fake_stretch)
    monkeypatch.setattr(dub.shutil, "rmtree", lambda path, ignore_errors=False: None)

    work_dir = tmp_path / "work"
    dub.dub_and_export(
        segments=[
            SubtitleSegment(start=0.0, end=1.5, text="cau mot", speaker=None),
            SubtitleSegment(start=2.0, end=3.0, text="cau hai", speaker=None),
        ],
        target_language="vi",
        source_video=tmp_path / "input.mp4",
        work_dir=work_dir,
        out_dir=tmp_path / "out",
        stem="input",
    )

    segment_dir = work_dir / "dub_vi_segments"
    assert stretch_calls == [(segment_dir / "00000_raw.wav", segment_dir / "00000_fit.wav", 2.0)]
    # Clip 1 dung ban da tang toc, clip 2 (vua khoang trong) giu nguyen ban raw.
    assert captured["clips"] == [
        (0.0, segment_dir / "00000_fit.wav"),
        (2.0, segment_dir / "00001_raw.wav"),
    ]


def test_dub_keeps_raw_clip_when_stretch_fails(tmp_path, monkeypatch):
    captured = {}

    class FakeTTS:
        def __init__(self, language: str, voice: str | None = None, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def synthesize(self, text: str, output_path: Path) -> None:
            output_path.write_bytes(b"fake wav")

    def broken_stretch(input_path, output_path, target_duration):
        raise RuntimeError("ffmpeg loi gia lap")

    monkeypatch.setattr(dub, "EdgeTTSSynthesizer", FakeTTS)
    monkeypatch.setattr(dub, "build_dub_track", lambda *a, **k: captured.update(clips=a[0]))
    monkeypatch.setattr(
        dub, "mux_audio_into_video", lambda *a, **k: a[2].write_bytes(b"fake video")
    )
    monkeypatch.setattr(dub, "_total_duration", lambda work_dir, source_video: 1.0)
    monkeypatch.setattr(dub, "_clip_duration_seconds", lambda path: 5.0)
    monkeypatch.setattr(dub, "time_stretch_to_duration", broken_stretch)
    monkeypatch.setattr(dub.shutil, "rmtree", lambda path, ignore_errors=False: None)

    work_dir = tmp_path / "work"
    dub.dub_and_export(
        segments=[SubtitleSegment(start=0.0, end=1.0, text="xin chao", speaker=None)],
        target_language="vi",
        source_video=tmp_path / "input.mp4",
        work_dir=work_dir,
        out_dir=tmp_path / "out",
        stem="input",
    )

    # Loi stretch khong lam fail job - dung lai ban raw.
    assert captured["clips"] == [(0.0, work_dir / "dub_vi_segments" / "00000_raw.wav")]


def test_dub_uses_raw_clips_without_stretching(tmp_path, monkeypatch):
    captured = {}

    class FakeTTS:
        sample_rate = 24000

        def __init__(self, language: str, voice: str | None = None, **kwargs):
            self.language = language
            self.voice = voice

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

    def fake_mux_audio_into_video(video_path, audio_path, output_path, **kwargs):
        output_path.write_bytes(b"fake video")

    monkeypatch.setattr(dub, "EdgeTTSSynthesizer", FakeTTS)
    monkeypatch.setattr(dub, "build_dub_track", fake_build_dub_track)
    monkeypatch.setattr(dub, "mux_audio_into_video", fake_mux_audio_into_video)
    monkeypatch.setattr(dub, "_total_duration", lambda work_dir, source_video: 3.0)
    monkeypatch.setattr(dub, "_clip_duration_seconds", lambda path: 0.4)
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


def test_dub_creates_one_synthesizer_per_distinct_speaker(tmp_path, monkeypatch):
    created_voices: list[str | None] = []

    class FakeTTS:
        sample_rate = 24000

        def __init__(self, language: str, voice: str | None = None, **kwargs):
            created_voices.append(voice)
            self.voice = voice

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def synthesize(self, text: str, output_path: Path) -> None:
            output_path.write_bytes(b"fake wav")

    monkeypatch.setattr(dub, "EdgeTTSSynthesizer", FakeTTS)
    monkeypatch.setattr(dub, "build_dub_track", lambda *a, **k: a[-1].write_bytes(b"fake track"))
    monkeypatch.setattr(
        dub, "mux_audio_into_video", lambda *a, **k: a[2].write_bytes(b"fake video")
    )
    monkeypatch.setattr(dub, "_total_duration", lambda work_dir, source_video: 3.0)
    monkeypatch.setattr(dub, "_clip_duration_seconds", lambda path: 0.4)
    monkeypatch.setattr(dub.shutil, "rmtree", lambda path, ignore_errors=False: None)

    work_dir = tmp_path / "work"
    out_dir = tmp_path / "out"
    source_video = tmp_path / "input.mp4"
    source_video.write_bytes(b"fake")

    dub.dub_and_export(
        segments=[
            SubtitleSegment(start=0.0, end=1.0, text="hi", speaker="SPEAKER_00"),
            SubtitleSegment(start=1.0, end=2.0, text="hello", speaker="SPEAKER_01"),
            SubtitleSegment(start=2.0, end=3.0, text="again", speaker="SPEAKER_00"),
        ],
        target_language="vi",
        source_video=source_video,
        work_dir=work_dir,
        out_dir=out_dir,
        stem="input",
        options=DubRenderOptions(voice="vi-VN-HoaiMyNeural"),
    )

    # 2 nguoi noi khac nhau -> 2 synthesizer (SPEAKER_00 tai su dung, khong
    # tao lai lan thu 3 xuat hien).
    assert created_voices == ["vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"]


def test_dub_uses_single_cloned_voice_for_all_speakers_when_ref_audio_set(tmp_path, monkeypatch):
    created_refs: list[Path] = []

    class FakeCloneTTS:
        def __init__(self, ref_audio_path: Path):
            created_refs.append(ref_audio_path)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def synthesize(self, text: str, output_path: Path) -> None:
            output_path.write_bytes(b"fake wav")

    monkeypatch.setattr(dub, "VieNeuCloneSynthesizer", FakeCloneTTS)
    monkeypatch.setattr(dub, "build_dub_track", lambda *a, **k: a[-1].write_bytes(b"fake track"))
    monkeypatch.setattr(
        dub, "mux_audio_into_video", lambda *a, **k: a[2].write_bytes(b"fake video")
    )
    monkeypatch.setattr(dub, "_total_duration", lambda work_dir, source_video: 3.0)
    monkeypatch.setattr(dub, "_clip_duration_seconds", lambda path: 0.4)
    monkeypatch.setattr(dub.shutil, "rmtree", lambda path, ignore_errors=False: None)

    work_dir = tmp_path / "work"
    out_dir = tmp_path / "out"
    source_video = tmp_path / "input.mp4"
    source_video.write_bytes(b"fake")
    ref_audio = tmp_path / "ref.wav"
    ref_audio.write_bytes(b"fake ref")

    dub.dub_and_export(
        segments=[
            SubtitleSegment(start=0.0, end=1.0, text="hi", speaker="SPEAKER_00"),
            SubtitleSegment(start=1.0, end=2.0, text="hello", speaker="SPEAKER_01"),
        ],
        target_language="vi",
        source_video=source_video,
        work_dir=work_dir,
        out_dir=out_dir,
        stem="input",
        options=DubRenderOptions(voice="vi-VN-HoaiMyNeural", custom_voice_ref_audio=ref_audio),
    )

    # 1 synthesizer DUY NHAT du co 2 nguoi noi khac nhau - giong clone KHONG
    # xoay vong theo nguoi noi nhu edge-tts (xem _build_speaker_voice_map).
    assert created_refs == [ref_audio]
