from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.db import SessionLocal
from app.models import Booking, BookingStatus, TimeSlot, SlotStatus, utcnow
from app.schemas import BookingHoldRequest, BookingPublicResponse, AdminBookingListItem

router = APIRouter(tags=["bookings"])

SLOT_MINUTES = 15
HOLD_MINUTES = 30


def expire_holds(db):
    """
    Expire HELD slots whose hold_expires_at is in the past.
    Also marks related bookings as EXPIRED.
    """
    now = datetime.now(timezone.utc)

    expired_slots = db.execute(
        select(TimeSlot).where(
            TimeSlot.status == SlotStatus.HELD,
            TimeSlot.hold_expires_at.is_not(None),
            TimeSlot.hold_expires_at < now,
        )
    ).scalars().all()

    if not expired_slots:
        return

    expired_slot_ids = [s.id for s in expired_slots]

    db.execute(
        update(TimeSlot)
        .where(TimeSlot.id.in_(expired_slot_ids))
        .values(status=SlotStatus.FREE, hold_expires_at=None, updated_at=utcnow())
    )

    db.execute(
        update(Booking)
        .where(Booking.time_slot_id.in_(expired_slot_ids))
        .where(Booking.status.in_([BookingStatus.HOLD, BookingStatus.PENDING_PAYMENT]))
        .values(status=BookingStatus.EXPIRED, updated_at=utcnow())
    )

    db.commit()


@router.post("/bookings/hold", response_model=BookingPublicResponse)
def create_hold(payload: BookingHoldRequest):
    """
    Create a HOLD on a slot (FREE -> HELD) and create a booking with status HOLD.
    Requires that a TimeSlot row already exists for payload.start_at.
    """
    db = SessionLocal()
    try:
        expire_holds(db)

        start_at = payload.start_at.astimezone(timezone.utc)
        end_at = start_at + timedelta(minutes=SLOT_MINUTES)
        now = datetime.now(timezone.utc)
        hold_expires = now + timedelta(minutes=HOLD_MINUTES)

        slot = db.execute(
            select(TimeSlot).where(TimeSlot.start_at == start_at)
        ).scalar_one_or_none()

        if not slot:
            raise HTTPException(status_code=404, detail="Slot not found (generate slots first).")

        res = db.execute(
            update(TimeSlot)
            .where(TimeSlot.id == slot.id)
            .where(TimeSlot.status == SlotStatus.FREE)
            .values(status=SlotStatus.HELD, hold_expires_at=hold_expires, updated_at=utcnow())
        )
        if res.rowcount != 1:
            db.rollback()
            raise HTTPException(status_code=409, detail="Slot already taken.")

        booking = Booking(
            time_slot_id=slot.id,
            customer_name=payload.customer_name,
            customer_email=str(payload.customer_email),
            customer_phone=payload.customer_phone,
            description=payload.description,
            status=BookingStatus.HOLD,
            stripe_payment_intent_id=None,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        db.add(booking)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            db.execute(
                update(TimeSlot)
                .where(TimeSlot.id == slot.id)
                .values(status=SlotStatus.FREE, hold_expires_at=None, updated_at=utcnow())
            )
            db.commit()
            raise HTTPException(status_code=409, detail="Slot already booked.")

        db.refresh(booking)

        slot = db.execute(select(TimeSlot).where(TimeSlot.id == slot.id)).scalar_one()

        return BookingPublicResponse(
            id=booking.id,
            status=booking.status.value,
            start_at=slot.start_at,
            end_at=end_at,
            hold_expires_at=slot.hold_expires_at,
        )
    finally:
        db.close()


@router.get("/bookings/{booking_id}", response_model=BookingPublicResponse)
def get_booking_public(booking_id: int):
    """
    Public endpoint to read the booking status (useful for frontend polling after payment).
    """
    db = SessionLocal()
    try:
        expire_holds(db)

        b = db.execute(select(Booking).where(Booking.id == booking_id)).scalar_one_or_none()
        if not b:
            raise HTTPException(status_code=404, detail="Not found")

        s = db.execute(select(TimeSlot).where(TimeSlot.id == b.time_slot_id)).scalar_one()

        return BookingPublicResponse(
            id=b.id,
            status=b.status.value,
            start_at=s.start_at,
            end_at=s.start_at + timedelta(minutes=SLOT_MINUTES),
            hold_expires_at=s.hold_expires_at,
        )
    finally:
        db.close()


@router.get("/admin/bookings", response_model=list[AdminBookingListItem])
def admin_list_bookings(
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    status: str | None = None,
):
    """
    Admin list bookings (no auth yet in this MVP).
    Later you can protect this with JWT.
    """
    db = SessionLocal()
    try:
        expire_holds(db)

        q = (
            select(Booking, TimeSlot)
            .join(TimeSlot, TimeSlot.id == Booking.time_slot_id)
            .order_by(TimeSlot.start_at.desc())
        )

        if start_at:
            if start_at.tzinfo is None:
                raise HTTPException(status_code=400, detail="start_at must be timezone-aware")
            q = q.where(TimeSlot.start_at >= start_at.astimezone(timezone.utc))

        if end_at:
            if end_at.tzinfo is None:
                raise HTTPException(status_code=400, detail="end_at must be timezone-aware")
            q = q.where(TimeSlot.start_at <= end_at.astimezone(timezone.utc))

        if status:
            try:
                q = q.where(Booking.status == BookingStatus(status))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid status")

        rows = db.execute(q).all()

        out: list[AdminBookingListItem] = []
        for b, s in rows:
            out.append(
                AdminBookingListItem(
                    id=b.id,
                    status=b.status.value,
                    start_at=s.start_at,
                    end_at=s.start_at + timedelta(minutes=SLOT_MINUTES),
                    customer_name=b.customer_name,
                    customer_email=b.customer_email,
                    customer_phone=b.customer_phone,
                    stripe_payment_intent_id=b.stripe_payment_intent_id,
                )
            )
        return out
    finally:
        db.close()


@router.post("/admin/bookings/{booking_id}/cancel")
def admin_cancel_booking(booking_id: int):
    """
    Cancel a booking. If the slot is BOOKED or HELD, free it.
    (No refunds handled in MVP.)
    """
    db = SessionLocal()
    try:
        expire_holds(db)

        b = db.execute(select(Booking).where(Booking.id == booking_id)).scalar_one_or_none()
        if not b:
            raise HTTPException(status_code=404, detail="Not found")

        slot = db.execute(select(TimeSlot).where(TimeSlot.id == b.time_slot_id)).scalar_one()

        if slot.status in (SlotStatus.BOOKED, SlotStatus.HELD):
            slot.status = SlotStatus.FREE
            slot.hold_expires_at = None
            slot.updated_at = utcnow()

        b.status = BookingStatus.CANCELLED
        b.updated_at = utcnow()

        db.commit()
        return {"ok": True}
    finally:
        db.close()