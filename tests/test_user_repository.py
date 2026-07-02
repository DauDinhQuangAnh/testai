"""Test UserRepository bang SQLite in-memory - khong can Postgres that chay."""
from app.auth.repository import UserRepository
from app.db.session import make_session_factory


def _make_repo() -> UserRepository:
    return UserRepository(session_factory=make_session_factory("sqlite:///:memory:"))


def test_create_and_get_by_email():
    repo = _make_repo()
    user = repo.create(email="a@example.com", password_hash="hashed")

    fetched = repo.get_by_email("a@example.com")

    assert fetched is not None
    assert fetched.id == user.id


def test_get_by_email_unknown_returns_none():
    repo = _make_repo()

    assert repo.get_by_email("nope@example.com") is None


def test_get_by_id():
    repo = _make_repo()
    user = repo.create(email="b@example.com", password_hash="hashed")

    fetched = repo.get_by_id(user.id)

    assert fetched is not None
    assert fetched.email == "b@example.com"
