"""Test probe_reference_seconds - ham thuan doc metadata audio (khong can
model VieNeu-TTS that/GPU - xem infrastructure/tts_vieneu.py). Adapter
`VieNeuCloneSynthesizer` da duoc verify THAT bang spike thu cong rieng
(tai model that, clone giong that tu 1 clip edge-tts sinh ra, xac nhan audio
dau ra hop le) - xem HANDOFF.md muc 6p, khong lap lai o day vi can tai model
~vai tram MB tu HuggingFace, khong phu hop chay trong CI/pytest thuong xuyen.
"""

import numpy as np
import soundfile as sf

from subtitle_pipeline.infrastructure.tts_vieneu import probe_reference_seconds


def test_probe_reference_seconds_returns_correct_duration(tmp_path):
    path = tmp_path / "ref.wav"
    sample_rate = 24000
    sf.write(str(path), np.zeros(sample_rate * 2, dtype=np.float32), sample_rate)

    assert probe_reference_seconds(path) == 2.0
