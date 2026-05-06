from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from auth.service import get_current_user
from billing import stripe_service
from config import settings
from db.database import get_db
from db.models import Plan, User

router = APIRouter(prefix="/billing", tags=["billing"])

@router.post("/subscribe")
async def create_subscription(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not settings.STRIPE_PRICE_ID_PRO:
        raise HTTPException(500, "Stripe not configured")
    if not current_user.stripe_customer_id:
        cid = stripe_service.create_customer(current_user.email, current_user.id)
        current_user.stripe_customer_id = cid
        db.commit()
    result = stripe_service.create_subscription(current_user.stripe_customer_id, settings.STRIPE_PRICE_ID_PRO)
    return {"client_secret": result["client_secret"], "subscription_id": result["subscription_id"]}

@router.get("/subscription")
async def get_subscription_info(current_user: User = Depends(get_current_user)):
    if not current_user.stripe_subscription_id:
        return {"plan": current_user.plan.value, "status": "no_subscription"}
    info = stripe_service.get_subscription(current_user.stripe_subscription_id)
    return {"plan": current_user.plan.value, "status": info["status"], "period_end": info["current_period_end"], "cancel_at_period_end": info["cancel_at_period_end"]}

@router.post("/cancel")
async def cancel_subscription(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.stripe_subscription_id:
        raise HTTPException(404, "No active subscription")
    stripe_service.cancel_subscription(current_user.stripe_subscription_id)
    current_user.subscription_status = "canceling"
    db.commit()
    return {"message": "Subscription will cancel at period end"}

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    result = stripe_service.handle_webhook(payload, sig_header)
    if "error" in result:
        raise HTTPException(400, result["error"])
    if result["action"] == "subscription_created" and result.get("user_id"):
        user = db.query(User).filter(User.id == int(result["user_id"])).first()
        if user:
            user.plan = Plan.PRO
            user.stripe_subscription_id = result["subscription_id"]
            user.subscription_status = "active"
            db.commit()
    elif result["action"] == "subscription_updated":
        user = db.query(User).filter(User.stripe_subscription_id == result["subscription_id"]).first()
        if user:
            user.subscription_status = result["status"]
            if result["status"] == "active":
                user.plan = Plan.PRO
            db.commit()
    elif result["action"] == "subscription_cancelled":
        user = db.query(User).filter(User.stripe_subscription_id == result["subscription_id"]).first()
        if user:
            user.plan = Plan.FREE
            user.subscription_status = "canceled"
            user.stripe_subscription_id = None
            db.commit()
    return JSONResponse({"received": True})
