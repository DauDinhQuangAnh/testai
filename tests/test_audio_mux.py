"""Test build_dub_track - dung soundfile/numpy tao clip gia, khong can model
TTS/ffmpeg that.
"""

from pathlib import Path

import numpy as np
import soundfile as sf

from subtitle_pipeline.infrastructure.audio_mux import build_dub_track


def test_clips_placed_at_correct_offset(tmp_path: Path):
    sample_rate = 1000
    clip_a = tmp_path / "a.wav"
    clip_b = tmp_path / "b.wav"
    sf.write(clip_a, np.ones(200, dtype=np.float32), sample_rate)
    sf.write(clip_b, np.full(100, 0.5, dtype=np.float32), sample_rate)

    output_path = tmp_path / "track.wav"
    build_dub_track(
        clips=[(0.0, clip_a), (0.5, clip_b)],
        total_duration=1.0,
        sample_rate=sample_rate,
        output_path=output_path,
    )

    track, rate = sf.read(output_path, dtype="float32")
    assert rate == sample_rate
    assert len(track) == sample_rate
    # atol noi long vi soundfile ghi wav mac dinh o PCM_16 (co sai so luong tu
    # hoa ~1/32768 khi doc lai), khong phai loi logic dat clip sai vi tri.
    assert np.allclose(track[:200], 1.0, atol=1e-3)
    assert np.allclose(track[500:600], 0.5, atol=1e-3)
    assert np.allclose(track[600:], 0.0, atol=1e-3)


def test_clip_beyond_total_duration_is_dropped(tmp_path: Path):
    sample_rate = 1000
    clip = tmp_path / "late.wav"
    sf.write(clip, np.ones(50, dtype=np.float32), sample_rate)

    output_path = tmp_path / "track.wav"
    build_dub_track(
        clips=[(5.0, clip)],
        total_duration=1.0,
        sample_rate=sample_rate,
        output_path=output_path,
    )

    track, _ = sf.read(output_path, dtype="float32")
    assert np.allclose(track, 0.0)
