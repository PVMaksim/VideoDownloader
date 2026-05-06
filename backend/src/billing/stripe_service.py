import stripe

from config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_customer(email: str, user_id: int) -> str:
    customer = stripe.Customer.create(email=email, metadata={"user_id": str(user_id)})
    return customer.id

def create_subscription(customer_id: str, price_id: str) -> dict:
    subscription = stripe.Subscription.create(
        customer=customer_id,
        items=[{"price": price_id}],
        payment_behavior="default_incomplete",
        expand=["latest_invoice.payment_intent"]
    )
    return {
        "subscription_id": subscription.id,
        "client_secret": subscription.latest_invoice.payment_intent.client_secret,
        "status": subscription.status
    }

def get_subscription(subscription_id: str) -> dict:
    sub = stripe.Subscription.retrieve(subscription_id)
    return {"status": sub.status, "current_period_end": sub.current_period_end, "cancel_at_period_end": sub.cancel_at_period_end}

def cancel_subscription(subscription_id: str) -> bool:
    sub = stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)
    return sub.cancel_at_period_end

def handle_webhook(payload: bytes, sig_header: str) -> dict:
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        return {"error": "Invalid webhook"}
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        return {"action": "subscription_created", "user_id": session.get("metadata", {}).get("user_id"), "subscription_id": session.get("subscription")}
    elif event["type"] == "customer.subscription.updated":
        sub = event["data"]["object"]
        return {"action": "subscription_updated", "subscription_id": sub.id, "status": sub.status, "period_end": sub.current_period_end}
    elif event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        return {"action": "subscription_cancelled", "subscription_id": sub.id}
    return {"action": "ignored", "type": event["type"]}
