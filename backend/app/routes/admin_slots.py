from datetime import datetime, timedelta, timezone, time as dtime

from fastapi import APIRouter, Query
from sqlalchemy.exc import IntegrityError

from app.db import SessionLocal
from app.models import TimeSlot, SlotStatus, utcnow

router = APIRouter(prefix="/admin/slots", tags=["admin-slots"])

SLOT_MINUTES = 15


@router.post("/generate")
def generate_slots(days: int = Query(30, ge=1, le=365)):
    """
    Simple slot generator for MVP:
    - Generates slots every 15 minutes
    - For the next `days`
    - Window: 11:00-19:00 UTC
    """
    db = SessionLocal()
    created = 0
    skipped = 0
    try:
        now = datetime.now(timezone.utc)
        start_day = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

        work_start = dtime(11, 0)
        work_end = dtime(19, 0)

        for d in range(days):
            day = start_day + timedelta(days=d)
            t = datetime.combine(day.date(), work_start, tzinfo=timezone.utc)
            end = datetime.combine(day.date(), work_end, tzinfo=timezone.utc)

            while t < end:
                slot = TimeSlot(
                    start_at=t,
                    status=SlotStatus.FREE,
                    hold_expires_at=None,
                    created_at=utcnow(),
                    updated_at=utcnow(),
                )
                db.add(slot)
                try:
                    db.commit()
                    created += 1
                except IntegrityError:
                    db.rollback()
                    skipped += 1

                t += timedelta(minutes=SLOT_MINUTES)

        return {"created": created, "skipped_existing": skipped}
    finally:
        db.close()