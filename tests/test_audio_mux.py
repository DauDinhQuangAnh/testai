"""Test build_dub_track + _build_mux_command - dung soundfile/numpy tao clip
gia va kiem tra lenh ffmpeg duoc dung dung, khong can model TTS/ffmpeg that.
"""

from pathlib import Path

import numpy as np
import soundfile as sf

from subtitle_pipeline.infrastructure.audio_mux import (
    _build_burn_command,
    _build_mux_command,
    build_dub_track,
)


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


def test_overlapping_clips_are_mixed_not_clobbered(tmp_path: Path):
    sample_rate = 1000
    clip_a = tmp_path / "a.wav"
    clip_b = tmp_path / "b.wav"
    sf.write(clip_a, np.full(400, 0.25, dtype=np.float32), sample_rate)
    sf.write(clip_b, np.full(100, 0.5, dtype=np.float32), sample_rate)

    output_path = tmp_path / "track.wav"
    build_dub_track(
        clips=[(0.0, clip_a), (0.2, clip_b)],
        total_duration=1.0,
        sample_rate=sample_rate,
        output_path=output_path,
    )

    track, _ = sf.read(output_path, dtype="float32")
    # Doan chong lan (0.2s-0.3s): 2 clip cong don, khong clip nao bi cat.
    assert np.allclose(track[200:300], 0.75, atol=1e-3)
    # Duoi clip A sau khi clip B ket thuc van con nguyen (khong bi ghi de mat).
    assert np.allclose(track[300:400], 0.25, atol=1e-3)


def test_summed_overlap_is_clipped_to_valid_range(tmp_path: Path):
    sample_rate = 1000
    clip_a = tmp_path / "a.wav"
    clip_b = tmp_path / "b.wav"
    sf.write(clip_a, np.full(100, 0.8, dtype=np.float32), sample_rate)
    sf.write(clip_b, np.full(100, 0.8, dtype=np.float32), sample_rate)

    output_path = tmp_path / "track.wav"
    build_dub_track(
        clips=[(0.0, clip_a), (0.0, clip_b)],
        total_duration=0.2,
        sample_rate=sample_rate,
        output_path=output_path,
    )

    track, _ = sf.read(output_path, dtype="float32")
    assert np.all(track <= 1.0)  # 0.8 + 0.8 bi clip ve 1.0, khong wrap/vo tieng


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


def test_mux_command_replace_mode_maps_dub_audio_only():
    cmd = _build_mux_command(Path("in.mp4"), Path("dub.wav"), Path("out.mp4"), original_volume=0.0)

    assert "-filter_complex" not in cmd
    assert cmd[cmd.index("-map") + 1] == "0:v:0"
    assert "1:a:0" in cmd


def test_mux_command_replace_mode_with_dub_volume_uses_filter():
    cmd = _build_mux_command(
        Path("in.mp4"), Path("dub.wav"), Path("out.mp4"), original_volume=0.0, dub_volume=1.2
    )

    filter_arg = cmd[cmd.index("-filter_complex") + 1]
    assert "volume=1.2" in filter_arg
    assert "[aout]" in cmd


def test_mux_command_keep_mode_mixes_with_reduced_original():
    cmd = _build_mux_command(Path("in.mp4"), Path("dub.wav"), Path("out.mp4"), original_volume=0.3)

    filter_arg = cmd[cmd.index("-filter_complex") + 1]
    assert "volume=0.3" in filter_arg
    assert "amix=inputs=2" in filter_arg
    assert "normalize=0" in filter_arg
    assert "[aout]" in cmd  # map audio da tron, khong phai track goc


def test_mux_command_ducking_uses_sidechain_and_asplit():
    cmd = _build_mux_command(
        Path("in.mp4"),
        Path("dub.wav"),
        Path("out.mp4"),
        original_volume=0.4,
        dub_volume=1.0,
        ducking=True,
    )

    filter_arg = cmd[cmd.index("-filter_complex") + 1]
    assert "sidechaincompress" in filter_arg
    # Track dub dung 2 lan (sidechain + tron output) nen phai asplit.
    assert "asplit=2" in filter_arg
    assert "amix=inputs=2" in filter_arg


def test_burn_command_uses_ass_filename_and_crf():
    cmd = _build_burn_command(Path("in.mp4"), "subs.ass", Path("out.mp4"), crf=18)

    assert cmd[cmd.index("-vf") + 1] == "ass=subs.ass"
    assert cmd[cmd.index("-crf") + 1] == "18"
    assert "libx264" in cmd
