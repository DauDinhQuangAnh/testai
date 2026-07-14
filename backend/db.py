"""Session factory dung chung cho toan backend - tao 1 lan (lazy) thay vi
goi `make_session_factory()` moi request (ham do tao engine + create_all,
rat nang neu lap lai). Test override bang `set_session_factory()` voi SQLite
in-memory (xem tests/test_backend_api.py).
"""

from sqlalchemy.orm import sessionmaker

from app.db.session import make_session_factory
from app.jobs.repository import JobRepository
from app.users.repository import UserRepository
from app.voices.repository import CustomVoiceRepository

_factory: sessionmaker | None = None


def get_session_factory() -> sessionmaker:
    global _factory
    if _factory is None:
        _factory = make_session_factory()
    return _factory


def set_session_factory(factory: sessionmaker | None) -> None:
    global _factory
    _factory = factory


def job_repo() -> JobRepository:
    return JobRepository(session_factory=get_session_factory())


def user_repo() -> UserRepository:
    return UserRepository(session_factory=get_session_factory())


def custom_voice_repo() -> CustomVoiceRepository:
    return CustomVoiceRepository(session_factory=get_session_factory())
