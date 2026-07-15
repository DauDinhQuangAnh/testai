"""Test GeminiTranslator (mock _call_api, khong goi mang) + logic chon
engine/fallback trong application/translate.py."""

import json

import pytest

import subtitle_pipeline.application.translate as translate_module
import subtitle_pipeline.infrastructure.translator_gemini as gemini_module
from subtitle_pipeline.domain.models import SubtitleSegment
from subtitle_pipeline.infrastructure.translator_gemini import (
    BATCH_SIZE,
    GeminiTranslator,
    _build_prompt,
    _parse_batch_response,
)


def _make_translator(monkeypatch) -> GeminiTranslator:
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    return GeminiTranslator("en", "vi")


def test_init_without_api_key_raises(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ValueError):
        GeminiTranslator("en", "vi")


def test_prompt_contains_language_names_and_lines():
    prompt = _build_prompt(["hello", "goodbye"], "en", "vi")

    assert "English" in prompt
    assert "Vietnamese" in prompt
    assert '"hello"' in prompt
    assert "exactly 2 elements" in prompt


def test_prompt_falls_back_to_raw_code_for_unknown_language():
    prompt = _build_prompt(["hej"], "sv", "vi")

    assert "from sv to Vietnamese" in prompt


def test_parse_batch_response_rejects_wrong_length():
    with pytest.raises(ValueError):
        _parse_batch_response(json.dumps(["mot"]), expected_count=2)


def test_parse_batch_response_rejects_non_array():
    with pytest.raises(ValueError):
        _parse_batch_response(json.dumps({"a": 1}), expected_count=1)


def test_translate_maps_texts_and_keeps_timing(monkeypatch):
    translator = _make_translator(monkeypatch)
    monkeypatch.setattr(
        translator, "_call_api", lambda prompt: json.dumps(["xin chào", "tạm biệt"])
    )

    segments = [
        SubtitleSegment(start=0.0, end=1.0, text="hello", speaker="SPEAKER_00"),
        SubtitleSegment(start=1.0, end=2.0, text="goodbye", speaker=None),
    ]
    result = translator.translate(segments)

    assert [seg.text for seg in result] == ["xin chào", "tạm biệt"]
    assert (result[0].start, result[0].end, result[0].speaker) == (0.0, 1.0, "SPEAKER_00")


def test_translate_splits_into_batches(monkeypatch):
    translator = _make_translator(monkeypatch)
    call_sizes: list[int] = []

    def fake_call(prompt: str) -> str:
        lines = json.loads(prompt[prompt.index("\n[") + 1 :])
        call_sizes.append(len(lines))
        return json.dumps([f"vi:{line}" for line in lines])

    monkeypatch.setattr(translator, "_call_api", fake_call)

    segments = [
        SubtitleSegment(start=float(i), end=float(i + 1), text=f"line {i}")
        for i in range(BATCH_SIZE + 5)
    ]
    result = translator.translate(segments)

    assert call_sizes == [BATCH_SIZE, 5]
    assert len(result) == BATCH_SIZE + 5
    assert result[-1].text == f"vi:line {BATCH_SIZE + 4}"


def test_translate_retries_then_raises(monkeypatch):
    translator = _make_translator(monkeypatch)
    monkeypatch.setattr(gemini_module, "RETRY_BACKOFF_SECONDS", 0.0)
    attempts = {"count": 0}

    def failing_call(prompt: str) -> str:
        attempts["count"] += 1
        raise OSError("mat mang gia lap")

    monkeypatch.setattr(translator, "_call_api", failing_call)

    with pytest.raises(RuntimeError):
        translator.translate([SubtitleSegment(start=0.0, end=1.0, text="hello")])
    assert attempts["count"] == gemini_module.MAX_ATTEMPTS


class _FakeNLLB:
    """Thay NLLBTranslator that (khong tai model) de test logic chon engine."""

    created = 0

    def __init__(self, source_language, target_language, device):
        _FakeNLLB.created += 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def translate(self, segments):
        return [
            SubtitleSegment(start=s.start, end=s.end, text=f"nllb:{s.text}", speaker=s.speaker)
            for s in segments
        ]


def test_translate_segments_uses_nllb_when_no_gemini_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(translate_module, "NLLBTranslator", _FakeNLLB)

    result = translate_module._translate_segments(
        [SubtitleSegment(start=0.0, end=1.0, text="hello")], "en", "vi", "cpu"
    )

    assert result[0].text == "nllb:hello"


def test_translate_segments_falls_back_to_nllb_when_gemini_fails(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(translate_module, "NLLBTranslator", _FakeNLLB)

    class BrokenGemini:
        def __init__(self, source_language, target_language):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def translate(self, segments):
            raise RuntimeError("quota het gia lap")

    monkeypatch.setattr(translate_module, "GeminiTranslator", BrokenGemini)

    result = translate_module._translate_segments(
        [SubtitleSegment(start=0.0, end=1.0, text="hello")], "en", "vi", "cpu"
    )

    assert result[0].text == "nllb:hello"


def test_translate_segments_uses_gemini_when_key_present(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(translate_module, "NLLBTranslator", _FakeNLLB)

    class WorkingGemini:
        def __init__(self, source_language, target_language):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def translate(self, segments):
            return [
                SubtitleSegment(start=s.start, end=s.end, text=f"gemini:{s.text}") for s in segments
            ]

    monkeypatch.setattr(translate_module, "GeminiTranslator", WorkingGemini)
    _FakeNLLB.created = 0

    result = translate_module._translate_segments(
        [SubtitleSegment(start=0.0, end=1.0, text="hello")], "en", "vi", "cpu"
    )

    assert result[0].text == "gemini:hello"
    assert _FakeNLLB.created == 0  # khong dung toi NLLB khi Gemini chay ngon
