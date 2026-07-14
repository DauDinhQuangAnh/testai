"""CRUD giong long tieng da clone - nguoi dung upload/ghi am 1 doan mau, luu
lai file tham chieu de dung lai nhieu lan (xem
subtitle_pipeline/infrastructure/tts_vieneu.py + HANDOFF.md muc 6p). KHONG
luu speaker embedding vao DB - `VieNeuCloneSynthesizer` tu ma hoa lai
`ref_audio_path` moi lan long tieng (1 lan/job, khong phai 1 lan/segment).
"""

import subprocess
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.config import AppConfig
from backend.db import custom_voice_repo
from backend.schemas import CustomVoiceOut
from backend.security import AuthUser, get_current_user
from subtitle_pipeline.infrastructure.tts_vieneu import (
    MIN_REFERENCE_SECONDS,
    probe_reference_seconds,
)

router = APIRouter(prefix="/voices", tags=["voices"])

MAX_FILE_SIZE_MB = 20


def _voices_dir(user_id: str) -> Path:
    return AppConfig.from_env().storage_dir / "custom_voices" / user_id


def get_owned_voice(voice_id: str, user: AuthUser):
    voice = custom_voice_repo().get(voice_id)
    if voice is None or voice.user_id != user.id:
        raise HTTPException(status_code=404, detail="Không tìm thấy giọng đã clone")
    return voice


@router.post("", response_model=CustomVoiceOut)
def create_voice(
    name: str = Form(...),
    file: UploadFile = File(...),
    user: AuthUser = Depends(get_current_user),
) -> CustomVoiceOut:
    if not name.strip():
        raise HTTPException(status_code=400, detail="Cần đặt tên cho giọng")
    data = file.file.read()
    if len(data) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File quá {MAX_FILE_SIZE_MB}MB")

    voice_id = str(uuid.uuid4())
    voice_dir = _voices_dir(user.id)
    voice_dir.mkdir(parents=True, exist_ok=True)
    upload_suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    raw_path = voice_dir / f"{voice_id}_raw{upload_suffix}"
    raw_path.write_bytes(data)

    ref_path = voice_dir / f"{voice_id}.wav"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(raw_path), "-ar", "24000", "-ac", "1", str(ref_path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise HTTPException(
            status_code=400, detail=f"Không đọc được file âm thanh: {exc.stderr}"
        ) from exc
    finally:
        raw_path.unlink(missing_ok=True)

    duration = probe_reference_seconds(ref_path)
    if duration < MIN_REFERENCE_SECONDS:
        ref_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=(
                f"Đoạn ghi quá ngắn ({duration:.1f} giây) - cần đọc tối thiểu "
                f"{MIN_REFERENCE_SECONDS:.0f} giây."
            ),
        )

    voice = custom_voice_repo().create(
        user_id=user.id, name=name.strip(), ref_audio_path=str(ref_path)
    )
    return CustomVoiceOut.from_voice(voice)


@router.get("", response_model=list[CustomVoiceOut])
def list_voices(user: AuthUser = Depends(get_current_user)) -> list[CustomVoiceOut]:
    return [CustomVoiceOut.from_voice(v) for v in custom_voice_repo().list_by_user(user.id)]


@router.delete("/{voice_id}")
def delete_voice(voice_id: str, user: AuthUser = Depends(get_current_user)) -> dict:
    voice = get_owned_voice(voice_id, user)
    Path(voice.ref_audio_path).unlink(missing_ok=True)
    custom_voice_repo().delete(voice_id)
    return {"deleted": voice_id}
