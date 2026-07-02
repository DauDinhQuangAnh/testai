"""FastAPI toi gian CHI de nhan webhook tu Stripe - ngoai le duy nhat can HTTP
API that trong kien truc Streamlit-only (xem HANDOFF.md quyet dinh kien truc
muc 2). Khong lien quan gi den luong Streamlit chinh.

Chay rieng: uvicorn app.billing.webhook_app:app --port 8001
Cau hinh Stripe Dashboard tro webhook toi: https://<domain-that>/stripe/webhook

CHUA duoc kiem thu voi Stripe that (khong co credential trong moi truong viet
code - xem HANDOFF.md Phase 7).
"""
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException, Request

from app.billing.repository import SubscriptionRepository
from app.billing.stripe_service import verify_webhook_event
from app.db.models import PlanTier

app = FastAPI(title="AI Subtitle Studio - Stripe Webhook")

SUBSCRIPTION_ACTIVE_EVENTS = {"customer.subscription.created", "customer.subscription.updated"}


@app.post("/stripe/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)) -> dict:
    payload = await request.body()
    try:
        event = verify_webhook_event(payload, stripe_signature)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid webhook signature: {exc}") from exc

    repo = SubscriptionRepository()
    data = event["data"]["object"]
    user_id = (data.get("metadata") or {}).get("user_id")

    if event["type"] in SUBSCRIPTION_ACTIVE_EVENTS and user_id:
        period_end = datetime.fromtimestamp(data["current_period_end"], tz=timezone.utc)
        repo.upsert(
            user_id=user_id,
            plan=PlanTier.PRO,
            stripe_customer_id=data["customer"],
            stripe_subscription_id=data["id"],
            current_period_end=period_end,
        )
    elif event["type"] == "customer.subscription.deleted" and user_id:
        repo.downgrade_to_free(user_id)

    return {"status": "ok"}
