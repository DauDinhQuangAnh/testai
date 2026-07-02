"""Repository cho Subscription - cung mau thiet ke voi JobRepository/UserRepository."""
import uuid
from collections.abc import Callable
from datetime import datetime

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

    def upsert(
        self,
        user_id: str,
        plan: PlanTier,
        stripe_customer_id: str | None = None,
        stripe_subscription_id: str | None = None,
        current_period_end: datetime | None = None,
    ) -> Subscription:
        with self._session_factory() as session:
            sub = session.scalar(select(Subscription).where(Subscription.user_id == user_id))
            if sub is None:
                sub = Subscription(id=str(uuid.uuid4()), user_id=user_id)
                session.add(sub)
            sub.plan = plan
            if stripe_customer_id is not None:
                sub.stripe_customer_id = stripe_customer_id
            if stripe_subscription_id is not None:
                sub.stripe_subscription_id = stripe_subscription_id
            if current_period_end is not None:
                sub.current_period_end = current_period_end
            session.commit()
            session.refresh(sub)
            return sub

    def downgrade_to_free(self, user_id: str) -> None:
        self.upsert(user_id=user_id, plan=PlanTier.FREE)
