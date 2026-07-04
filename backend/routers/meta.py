"""Metadata cho wizard FE: ngon ngu, danh sach giong (kem de xuat/style),
nghe thu giong (goi edge-tts dong bo, can internet).
"""

from fastapi import APIRouter, Depends, HTTPException, Response

from backend.schemas import VoiceSampleIn
from backend.security import AuthUser, get_current_user
from subtitle_pipeline.infrastructure.translator_nllb import (
    NLLB_LANGUAGE_CODES,
    SUPPORTED_LANGUAGES,
)
from subtitle_pipeline.infrastructure.tts_edge import synthesize_sample, voice_catalog

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/languages")
def languages() -> dict:
    return {
        "targets": SUPPORTED_LANGUAGES,
        "sources": sorted(NLLB_LANGUAGE_CODES.keys()),
    }


@router.get("/voices/{language}")
def voices(language: str) -> list[dict]:
    try:
        return voice_catalog(language)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/voice-sample")
def voice_sample(body: VoiceSampleIn, user: AuthUser = Depends(get_current_user)) -> Response:
    try:
        audio = synthesize_sample(body.language, body.voice, body.rate_percent, body.pitch_hz)
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Không tạo được mẫu giọng (cần internet): {exc}"
        ) from exc
    return Response(content=audio, media_type="audio/mpeg")
