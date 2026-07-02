"""Wrapper goi Stripe API: tao Checkout Session va xac minh webhook. Can bien
moi truong STRIPE_SECRET_KEY / STRIPE_WEBHOOK_SECRET - neu chua co, cac ham o
day raise loi ro rang thay vi im lang that bai hoac goi API voi key rong.

CHUA duoc kiem thu voi tai khoan Stripe that (khong co credential trong moi
truong viet code). Xem HANDOFF.md Phase 7 truoc khi trien khai that.
"""
import os

import stripe


def _configured_client() -> type[stripe]:
    api_key = os.environ.get("STRIPE_SECRET_KEY")
    if not api_key:
        raise RuntimeError("STRIPE_SECRET_KEY chua duoc set - xem .env.example")
    stripe.api_key = api_key
    return stripe


def create_checkout_session(
    price_id: str, customer_email: str, success_url: str, cancel_url: str
) -> str:
    client = _configured_client()
    session = client.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        customer_email=customer_email,
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.url


def verify_webhook_event(payload: bytes, signature_header: str):
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET chua duoc set - xem .env.example")
    return stripe.Webhook.construct_event(payload, signature_header, webhook_secret)
