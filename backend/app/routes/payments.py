import os
from datetime import datetime, timezone, timedelta

import stripe
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select, update

from app.db import SessionLocal
from app.models import Booking, BookingStatus, TimeSlot, SlotStatus, utcnow
from app.schemas import CreatePaymentIntentRequest, CreatePaymentIntentResponse
from app.routes.bookings import expire_holds

router = APIRouter(prefix="/payments", tags=["payments"])

# Fixed deposit: $500 MXN -> Stripe expects smallest currency unit (cents)
DEPOSIT_AMOUNT_MXN_CENTS = 50000
CURRENCY = "mxn"


def _stripe_init():
    secret = os.getenv("STRIPE_SECRET_KEY")
    if not secret:
        raise HTTPException(status_code=500, detail="Missing STRIPE_SECRET_KEY")
    stripe.api_key = secret


@router.post("/intent", response_model=CreatePaymentIntentResponse)
def create_payment_intent(payload: CreatePaymentIntentRequest):
    """
    Creates a Stripe PaymentIntent for the fixed deposit (500 MXN).
    Only allowed if booking is HOLD (or PENDING_PAYMENT) and slot is still HELD and not expired.
    """
    _stripe_init()

    db = SessionLocal()
    try:
        expire_holds(db)

        booking = db.execute(
            select(Booking).where(Booking.id == payload.booking_id)
        ).scalar_one_or_none()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        if booking.status not in (BookingStatus.HOLD, BookingStatus.PENDING_PAYMENT):
            raise HTTPException(status_code=409, detail=f"Booking not payable in status {booking.status.value}")

        slot = db.execute(select(TimeSlot).where(TimeSlot.id == booking.time_slot_id)).scalar_one()
        if slot.status != SlotStatus.HELD:
            raise HTTPException(status_code=409, detail="Slot is not on hold anymore")

        # Ensure not expired (defense in depth)
        now = datetime.now(timezone.utc)
        if slot.hold_expires_at and slot.hold_expires_at < now:
            raise HTTPException(status_code=409, detail="Hold expired")

        # Create PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=DEPOSIT_AMOUNT_MXN_CENTS,
            currency=CURRENCY,
            automatic_payment_methods={"enabled": True},
            metadata={
                "booking_id": str(booking.id),
                "time_slot_id": str(slot.id),
            },
        )

        # Mark as pending payment and store intent id
        booking.status = BookingStatus.PENDING_PAYMENT
        booking.stripe_payment_intent_id = intent.id
        booking.updated_at = utcnow()
        db.commit()

        return CreatePaymentIntentResponse(client_secret=intent.client_secret)
    finally:
        db.close()


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Stripe webhook endpoint. Confirms bookings only on payment_intent.succeeded.
    Verifies Stripe-Signature using STRIPE_WEBHOOK_SECRET.
    """
    _stripe_init()

    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Missing STRIPE_WEBHOOK_SECRET")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payload")

    # Handle event
    if event["type"] == "payment_intent.succeeded":
        pi = event["data"]["object"]
        booking_id = (pi.get("metadata") or {}).get("booking_id")
        if booking_id:
            db = SessionLocal()
            try:
                expire_holds(db)

                booking = db.execute(
                    select(Booking).where(Booking.id == int(booking_id))
                ).scalar_one_or_none()
                if not booking:
                    return {"ok": True}  # nothing to do

                # Only confirm if still pending/hold
                if booking.status not in (BookingStatus.HOLD, BookingStatus.PENDING_PAYMENT):
                    return {"ok": True}

                slot = db.execute(select(TimeSlot).where(TimeSlot.id == booking.time_slot_id)).scalar_one()

                # Confirm only if slot is still HELD
                now = datetime.now(timezone.utc)
                if slot.status != SlotStatus.HELD:
                    return {"ok": True}
                if slot.hold_expires_at and slot.hold_expires_at < now:
                    # expired - don't confirm
                    booking.status = BookingStatus.EXPIRED
                    booking.updated_at = utcnow()
                    db.commit()
                    return {"ok": True}

                # Confirm booking + book the slot
                slot.status = SlotStatus.BOOKED
                slot.hold_expires_at = None
                slot.updated_at = utcnow()

                booking.status = BookingStatus.CONFIRMED
                booking.stripe_payment_intent_id = pi.get("id")
                booking.updated_at = utcnow()

                db.commit()
            finally:
                db.close()

    return {"ok": True}