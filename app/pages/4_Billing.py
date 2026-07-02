"""Trang xem goi cuoc hien tai va usage trong thang. Khong co thanh toan tu
dong trong app (quyet dinh 2026-07-02) - nang cap goi lam thu cong qua DB,
xem app/billing/plans.py.
"""
import sys
from pathlib import Path

import streamlit as st

for _parent in Path(__file__).resolve().parents:
    if (_parent / "pyproject.toml").exists():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from app.auth.streamlit_helpers import require_login
from app.billing.plans import PLAN_CATALOG
from app.billing.repository import SubscriptionRepository
from app.billing.usage import monthly_minutes_used
from app.db.models import PlanTier
from app.jobs.repository import JobRepository

st.set_page_config(page_title="Billing - AI Subtitle Studio")
user = require_login()
st.title("Goi cuoc")

subscription = SubscriptionRepository().get_by_user(user.id)
current_plan = subscription.plan if subscription else PlanTier.FREE

minutes_used = monthly_minutes_used(JobRepository().list_by_user(user.id))
plan_info = PLAN_CATALOG[current_plan]

st.write(f"Goi hien tai: **{plan_info.name}**")
st.progress(
    min(minutes_used / plan_info.monthly_minutes_limit, 1.0),
    text=f"Da dung {minutes_used:.1f} / {plan_info.monthly_minutes_limit:.0f} phut trong thang",
)

if current_plan == PlanTier.FREE:
    st.info(
        "Muon nang len goi Pro (1000 phut/thang)? Lien he quan tri vien - "
        "hien chua ho tro thanh toan truc tiep trong app."
    )
