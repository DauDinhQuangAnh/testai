"""Repository cho User - cung mau thiet ke voi JobRepository (constructor
injection session_factory de test bang SQLite in-memory, xem
tests/test_user_repository.py)."""
import uuid
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import make_session_factory


class UserRepository:
    def __init__(self, session_factory: Callable[[], Session] | None = None):
        self._session_factory = session_factory or make_session_factory()

    def create(self, email: str, password_hash: str) -> User:
        with self._session_factory() as session:
            user = User(id=str(uuid.uuid4()), email=email, password_hash=password_hash)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def get_by_email(self, email: str) -> User | None:
        with self._session_factory() as session:
            return session.scalar(select(User).where(User.email == email))

    def get_by_id(self, user_id: str) -> User | None:
        with self._session_factory() as session:
            return session.get(User, user_id)
