"""Dinh nghia goi cuoc va gioi han usage - dung de kiem tra truoc khi cho tao
job moi (xem usage.py va app/pages/1_Upload.py).

Khong co thanh toan tu dong trong app (quyet dinh 2026-07-02, xem HANDOFF.md):
nang user len goi PRO lam thu cong bang cach cap nhat bang `subscriptions`
trong DB (vd. qua `SubscriptionRepository.upsert`).
"""
from dataclasses import dataclass

from app.db.models import PlanTier


@dataclass(frozen=True)
class Plan:
    tier: PlanTier
    name: str
    monthly_minutes_limit: float


PLAN_CATALOG = {
    PlanTier.FREE: Plan(tier=PlanTier.FREE, name="Free", monthly_minutes_limit=30.0),
    PlanTier.PRO: Plan(tier=PlanTier.PRO, name="Pro", monthly_minutes_limit=1000.0),
}
