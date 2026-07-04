"""Test _clamp_atempo_factors - logic thuan, khong goi ffmpeg that."""

import pytest

from subtitle_pipeline.infrastructure.audio_timing import _clamp_atempo_factors


def _product(factors: list[float]) -> float:
    result = 1.0
    for f in factors:
        result *= f
    return result


def test_factor_within_range_stays_single():
    assert _clamp_atempo_factors(1.5) == pytest.approx([1.5])


def test_factor_above_two_is_chained():
    factors = _clamp_atempo_factors(5.0)
    assert all(0.5 <= f <= 2.0 for f in factors)
    assert _product(factors) == pytest.approx(5.0)


def test_factor_below_half_is_chained():
    factors = _clamp_atempo_factors(0.2)
    assert all(0.5 <= f <= 2.0 for f in factors)
    assert _product(factors) == pytest.approx(0.2)


def test_zero_or_negative_factor_raises():
    with pytest.raises(ValueError):
        _clamp_atempo_factors(0.0)
    with pytest.raises(ValueError):
        _clamp_atempo_factors(-1.0)


def test_trim_command_cuts_first_seconds_with_stream_copy():
    from pathlib import Path

    from subtitle_pipeline.infrastructure.audio import _build_trim_command

    cmd = _build_trim_command(Path("in.mp4"), Path("out.mp4"), 60)

    assert cmd[cmd.index("-t") + 1] == "60"
    assert cmd[cmd.index("-c") + 1] == "copy"
