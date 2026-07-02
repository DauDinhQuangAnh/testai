"""Repository cho Subscription - cung mau thiet ke voi JobRepository/UserRepository.

Khong co thanh toan tu dong trong app: doi goi cho 1 user bang cach goi
`upsert(user_id, PlanTier.PRO)` thu cong (vd. tu 1 script quan tri hoac truc
tiep trong DB) - xem app/billing/plans.py.
"""
import uuid
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import PlanTier, Subscription
from app.db.session import make_session_factory


class SubscriptionRepository:
    def __init__(self, session_factory: Callable[[], Session] | None = None):
        self._session_factory = session_factory or make_session_factory()

    def get_by_user(self, user_id: str) -> Subscription | None:
        with self._session_factory() as session:
            return session.scalar(select(Subscription).where(Subscription.user_id == user_id))

    def upsert(self, user_id: str, plan: PlanTier) -> Subscription:
        with self._session_factory() as session:
            sub = session.scalar(select(Subscription).where(Subscription.user_id == user_id))
            if sub is None:
                sub = Subscription(id=str(uuid.uuid4()), user_id=user_id)
                session.add(sub)
            sub.plan = plan
            session.commit()
            session.refresh(sub)
            return sub
