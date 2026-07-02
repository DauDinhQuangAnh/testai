"""Dinh nghia goi cuoc va gioi han usage - dung de kiem tra truoc khi cho tao
job moi (xem usage.py va app/pages/1_Upload.py).
"""
import os
from dataclasses import dataclass

from app.db.models import PlanTier


@dataclass(frozen=True)
class Plan:
    tier: PlanTier
    name: str
    monthly_minutes_limit: float
    stripe_price_id: str | None


def get_plan_catalog() -> dict[PlanTier, Plan]:
    return {
        PlanTier.FREE: Plan(
            tier=PlanTier.FREE, name="Free", monthly_minutes_limit=30.0, stripe_price_id=None
        ),
        PlanTier.PRO: Plan(
            tier=PlanTier.PRO,
            name="Pro",
            monthly_minutes_limit=1000.0,
            stripe_price_id=os.environ.get("STRIPE_PRO_PRICE_ID"),
        ),
    }
