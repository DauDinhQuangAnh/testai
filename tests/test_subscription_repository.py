"""Test SubscriptionRepository bang SQLite in-memory."""
from app.billing.repository import SubscriptionRepository
from app.db.models import PlanTier
from app.db.session import make_session_factory


def _make_repo() -> SubscriptionRepository:
    return SubscriptionRepository(session_factory=make_session_factory("sqlite:///:memory:"))


def test_get_by_user_unknown_returns_none():
    repo = _make_repo()

    assert repo.get_by_user("user-1") is None


def test_upsert_creates_then_updates():
    repo = _make_repo()

    created = repo.upsert(user_id="user-1", plan=PlanTier.FREE)
    assert created.plan == PlanTier.FREE

    updated = repo.upsert(user_id="user-1", plan=PlanTier.PRO)
    assert updated.id == created.id
    assert updated.plan == PlanTier.PRO


def test_upsert_back_to_free():
    repo = _make_repo()
    repo.upsert(user_id="user-1", plan=PlanTier.PRO)

    repo.upsert(user_id="user-1", plan=PlanTier.FREE)

    assert repo.get_by_user("user-1").plan == PlanTier.FREE
