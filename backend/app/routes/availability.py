from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.db import SessionLocal
from app.models import TimeSlot, SlotStatus
from app.schemas import AvailabilityDayResponse, AvailabilitySlot
from app.routes.bookings import expire_holds  # <-- para limpiar holds vencidos

router = APIRouter(prefix="/availability", tags=["availability"])

SLOT_MINUTES = 15


@router.get("", response_model=AvailabilityDayResponse)
def get_availability(day: date = Query(..., description="Day in YYYY-MM-DD")):
    """
    Returns all FREE slots for the given day (UTC).
    Also expires any old holds so availability stays accurate.
    """
    db = SessionLocal()
    try:
        expire_holds(db)

        start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        slots = db.execute(
            select(TimeSlot)
            .where(TimeSlot.start_at >= start)
            .where(TimeSlot.start_at < end)
            .where(TimeSlot.status == SlotStatus.FREE)
            .order_by(TimeSlot.start_at.asc())
        ).scalars().all()

        return AvailabilityDayResponse(
            day=day,
            slots=[
                AvailabilitySlot(
                    start_at=s.start_at,
                    end_at=s.start_at + timedelta(minutes=SLOT_MINUTES),
                )
                for s in slots
            ],
        )
    finally:
        db.close()