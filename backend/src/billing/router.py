"""
Billing endpoints — Stripe checkout and webhooks
"""
import logging
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.database import get_db
from db.models import User, Subscription, Plan
from auth.service import get_current_user

stripe.api_key = settings.STRIPE_SECRET_KEY

log = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])


# ── Схемы ────────────────────────────────────────────────────────

class CheckoutResponse(BaseModel):
    checkout_url: str


class PortalResponse(BaseModel):
    portal_url: str


class PlanResponse(BaseModel):
    plan: str
    status: str
    current_period_end: str | None
    cancel_at_period_end: bool


# ── Роуты ────────────────────────────────────────────────────────

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create Stripe Checkout session for Pro subscription"""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Платёжная система не настроена")

    # Создаём или берём существующего Stripe customer
    customer_id = await _get_or_create_customer(current_user, db)

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": settings.STRIPE_PRO_PRICE_ID, "quantity": 1}],
        success_url=f"{settings.FRONTEND_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.FRONTEND_URL}/pricing",
        metadata={"user_id": str(current_user.id)},
    )

    return CheckoutResponse(checkout_url=session.url)


@router.post("/portal", response_model=PortalResponse)
async def customer_portal(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create Stripe Customer Portal session (manage/cancel subscription)"""
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    sub = result.scalar_one_or_none()
    if not sub or not sub.stripe_customer_id:
        raise HTTPException(status_code=404, detail="Подписка не найдена")

    session = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=f"{settings.FRONTEND_URL}/settings",
    )
    return PortalResponse(portal_url=session.url)


@router.get("/plan", response_model=PlanResponse)
async def get_plan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user plan info"""
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    sub = result.scalar_one_or_none()

    return PlanResponse(
        plan=current_user.plan,
        status=sub.status if sub else "none",
        current_period_end=sub.current_period_end.isoformat() if sub and sub.current_period_end else None,
        cancel_at_period_end=sub.cancel_at_period_end if sub else False,
    )


# ── Stripe Webhook ────────────────────────────────────────────────

@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Неверная подпись вебхука")

    log.info(f"Stripe event: {event['type']}")

    if event["type"] == "checkout.session.completed":
        await _handle_checkout_completed(event["data"]["object"], db)

    elif event["type"] in ("customer.subscription.updated", "customer.subscription.deleted"):
        await _handle_subscription_updated(event["data"]["object"], db)

    return {"ok": True}


# ── Внутренние функции ────────────────────────────────────────────

async def _get_or_create_customer(user: User, db: AsyncSession) -> str:
    """Get existing Stripe customer ID or create new one"""
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    sub = result.scalar_one_or_none()

    if sub and sub.stripe_customer_id:
        return sub.stripe_customer_id

    customer = stripe.Customer.create(
        email=user.email,
        metadata={"user_id": str(user.id)},
    )
    return customer.id


async def _handle_checkout_completed(session_obj, db: AsyncSession):
    """Activate Pro plan after successful payment"""
    user_id = int(session_obj["metadata"]["user_id"])
    customer_id = session_obj["customer"]
    subscription_id = session_obj["subscription"]

    # Получаем детали подписки
    stripe_sub = stripe.Subscription.retrieve(subscription_id)

    from datetime import datetime, timezone
    period_end = datetime.fromtimestamp(
        stripe_sub["current_period_end"], tz=timezone.utc
    )

    # Обновляем или создаём Subscription
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    sub = result.scalar_one_or_none()

    if not sub:
        sub = Subscription(user_id=user_id)
        db.add(sub)

    sub.stripe_customer_id = customer_id
    sub.stripe_subscription_id = subscription_id
    sub.stripe_price_id = settings.STRIPE_PRO_PRICE_ID
    sub.status = "active"
    sub.current_period_end = period_end
    sub.cancel_at_period_end = False

    # Апгрейд плана
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.plan = Plan.PRO

    log.info(f"User {user_id} upgraded to Pro, expires {period_end}")


async def _handle_subscription_updated(stripe_sub, db: AsyncSession):
    """Update subscription status (renewal, cancellation)"""
    result = await db.execute(
        select(Subscription).where(
            Subscription.stripe_subscription_id == stripe_sub["id"]
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return

    from datetime import datetime, timezone
    sub.status = stripe_sub["status"]
    sub.cancel_at_period_end = stripe_sub["cancel_at_period_end"]
    sub.current_period_end = datetime.fromtimestamp(
        stripe_sub["current_period_end"], tz=timezone.utc
    )

    # Если подписка истекла — понижаем до Free
    if stripe_sub["status"] in ("canceled", "unpaid", "past_due"):
        result = await db.execute(
            select(User).where(User.id == sub.user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.plan = Plan.FREE
            log.info(f"User {sub.user_id} downgraded to Free")
