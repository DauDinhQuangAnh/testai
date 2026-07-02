"""Trang xem/nang cap goi cuoc. Tao Stripe Checkout Session va dua link cho
nguoi dung tu mo (hosted page cua Stripe) - Streamlit khong tu xu ly thanh
toan. CHUA duoc kiem thu voi Stripe that (xem HANDOFF.md Phase 7).
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
from app.billing.plans import get_plan_catalog
from app.billing.repository import SubscriptionRepository
from app.billing.stripe_service import create_checkout_session
from app.billing.usage import monthly_minutes_used
from app.db.models import PlanTier
from app.jobs.repository import JobRepository

st.set_page_config(page_title="Billing - AI Subtitle Studio")
user = require_login()
st.title("Goi cuoc")

subscription = SubscriptionRepository().get_by_user(user.id)
current_plan = subscription.plan if subscription else PlanTier.FREE

minutes_used = monthly_minutes_used(JobRepository().list_by_user(user.id))
plans = get_plan_catalog()
plan_info = plans[current_plan]

st.write(f"Goi hien tai: **{plan_info.name}**")
st.write(f"Da dung thang nay: **{minutes_used:.1f} / {plan_info.monthly_minutes_limit:.0f} phut**")

if current_plan == PlanTier.FREE:
    pro_plan = plans[PlanTier.PRO]
    st.subheader(f"Nang cap len {pro_plan.name}")
    if st.button("Nang cap"):
        if not pro_plan.stripe_price_id:
            st.error("STRIPE_PRO_PRICE_ID chua duoc cau hinh - xem .env.example.")
        else:
            checkout_url = create_checkout_session(
                price_id=pro_plan.stripe_price_id,
                customer_email=user.email,
                success_url="http://localhost:8501/Billing?checkout=success",
                cancel_url="http://localhost:8501/Billing?checkout=cancel",
            )
            st.link_button("Tiep tuc thanh toan tren Stripe", checkout_url)
