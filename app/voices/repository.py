"""Repository cho CustomVoice - cung mau voi JobRepository/UserRepository
(nhan session_factory qua constructor de test bang SQLite in-memory)."""

import uuid
from collections.abc import Callable, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CustomVoice
from app.db.session import make_session_factory


class CustomVoiceRepository:
    def __init__(self, session_factory: Callable[[], Session] | None = None):
        self._session_factory = session_factory or make_session_factory()

    def create(self, user_id: str, name: str, ref_audio_path: str) -> CustomVoice:
        with self._session_factory() as session:
            voice = CustomVoice(
                id=str(uuid.uuid4()), user_id=user_id, name=name, ref_audio_path=ref_audio_path
            )
            session.add(voice)
            session.commit()
            session.refresh(voice)
            return voice

    def get(self, voice_id: str) -> CustomVoice | None:
        with self._session_factory() as session:
            return session.get(CustomVoice, voice_id)

    def list_by_user(self, user_id: str) -> Sequence[CustomVoice]:
        with self._session_factory() as session:
            stmt = (
                select(CustomVoice)
                .where(CustomVoice.user_id == user_id)
                .order_by(CustomVoice.created_at.desc())
            )
            return session.scalars(stmt).all()

    def delete(self, voice_id: str) -> None:
        with self._session_factory() as session:
            voice = session.get(CustomVoice, voice_id)
            if voice is None:
                return
            session.delete(voice)
            session.commit()
