"""Adapter dich theo NGU CANH bang Google Gemini (LLM) - nang cap chat luong
so voi NLLB (translator_nllb.py) von dich tung cau roi rac, khong nhan duoc
chi dan giong dieu. Gemini nhan ca loat cau cua cung 1 video trong 1 request
nen giu duoc ngu canh xuyen suot + giong van noi tu nhien (yeu cau "dich theo
ngu canh kieu VietDub" ghi nhan tu HANDOFF.md muc 6j, truoc do chua lam duoc
vi can LLM).

Goi REST API `generateContent` truc tiep qua urllib (stdlib) thay vi SDK
`google-genai` - tranh them dependency chi de POST 1 endpoint JSON (cung ly
do backend/email_sender.py dung smtplib thay vi thu vien email ngoai).

CAN INTERNET + GEMINI_API_KEY (tao mien phi tai https://aistudio.google.com).
Neu thieu key hoac API loi, application/translate.py TU DONG fallback ve NLLB
local - tinh nang dich khong bao gio phu thuoc cung vao Gemini.
"""

import json
import os
import time
import urllib.error
import urllib.request

from subtitle_pipeline.domain.models import SubtitleSegment

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
# So cau moi request: du lon de giu ngu canh + it request (video 10 phut
# ~100-150 cau -> 3-4 request), du nho de khong cham gioi han output token.
BATCH_SIZE = 40
MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 2.0
REQUEST_TIMEOUT_SECONDS = 120

# Ten ngon ngu day du cho prompt - LLM hieu ten tieng Anh chinh xac hon ma
# ISO 2 chu cai tran (vd. "vi" de nham voi ten bien). Ngon ngu nguon la ket
# qua auto-detect cua Whisper nen co the la BAT KY ma nao - ma la se dung
# nguyen ma trong prompt, Gemini van hieu duoc phan lon.
LANGUAGE_NAMES = {
    "vi": "Vietnamese",
    "en": "English",
    "zh": "Chinese (Simplified)",
    "ja": "Japanese",
    "ko": "Korean",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "ru": "Russian",
    "it": "Italian",
    "pt": "Portuguese",
    "th": "Thai",
    "hi": "Hindi",
    "id": "Indonesian",
    "nl": "Dutch",
    "tr": "Turkish",
    "pl": "Polish",
    "ar": "Arabic",
    "uk": "Ukrainian",
}


def _language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code)


def _build_prompt(texts: list[str], source_language: str, target_language: str) -> str:
    lines_json = json.dumps(texts, ensure_ascii=False)
    return (
        "You are a professional subtitle translator. Translate the following "
        f"subtitle lines from {_language_name(source_language)} to "
        f"{_language_name(target_language)}.\n"
        "The lines come from ONE video in chronological order - use the "
        "surrounding lines as context so pronouns, terminology and tone stay "
        "consistent. Keep each translation natural and concise, like spoken "
        "dialogue. Do not merge, split, add or drop lines.\n"
        "Return ONLY a JSON array of translated strings with exactly "
        f"{len(texts)} elements, in the same order as the input.\n"
        f"Input lines (JSON array):\n{lines_json}"
    )


class GeminiTranslator:
    """Cung interface context-manager + `translate(segments)` voi
    NLLBTranslator de application/translate.py hoan doi 2 engine khong can
    biet khac biet ben trong. Khong co model local nao phai load/giai phong
    nen __enter__/__exit__ khong lam gi (giu de dung chung cau truc `with`).
    """

    def __init__(
        self,
        source_language: str,
        target_language: str,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not self._api_key:
            raise ValueError("Chưa cấu hình GEMINI_API_KEY (xem .env.example)")
        self._model = model or os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        self._source_language = source_language
        self._target_language = target_language

    def __enter__(self) -> "GeminiTranslator":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def translate(self, segments: list[SubtitleSegment]) -> list[SubtitleSegment]:
        translated: list[SubtitleSegment] = []
        for offset in range(0, len(segments), BATCH_SIZE):
            batch = segments[offset : offset + BATCH_SIZE]
            texts = self._translate_batch([seg.text for seg in batch])
            translated.extend(
                SubtitleSegment(start=seg.start, end=seg.end, text=text, speaker=seg.speaker)
                for seg, text in zip(batch, texts, strict=True)
            )
        return translated

    def _translate_batch(self, texts: list[str]) -> list[str]:
        prompt = _build_prompt(texts, self._source_language, self._target_language)
        last_error: Exception | None = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                raw = self._call_api(prompt)
                return _parse_batch_response(raw, expected_count=len(texts))
            except Exception as exc:  # loi mang/quota/JSON sai deu retry nhu nhau
                last_error = exc
                if attempt < MAX_ATTEMPTS:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)
        raise RuntimeError(f"Gemini dịch thất bại sau {MAX_ATTEMPTS} lần thử: {last_error}")

    def _call_api(self, prompt: str) -> str:
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            # response_mime_type ep Gemini tra JSON thuan (khong boc ```json),
            # temperature thap de ban dich on dinh giua cac lan chay.
            "generationConfig": {"response_mime_type": "application/json", "temperature": 0.2},
        }
        request = urllib.request.Request(
            GEMINI_API_URL.format(model=self._model),
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": self._api_key},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload["candidates"][0]["content"]["parts"][0]["text"]


def _parse_batch_response(raw: str, expected_count: int) -> list[str]:
    parsed = json.loads(raw)
    if not isinstance(parsed, list) or len(parsed) != expected_count:
        raise ValueError(
            f"Gemini trả về {len(parsed) if isinstance(parsed, list) else 'không phải mảng'} "
            f"phần tử, cần đúng {expected_count}"
        )
    return [str(item) for item in parsed]
