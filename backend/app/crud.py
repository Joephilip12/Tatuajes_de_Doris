from __future__ import annotations

from datetime import datetime, timedelta, timezone, date
from typing import List, Tuple

from sqlalchemy import select, and_, update
from sqlalchemy.orm import Session

from app.models import (
    BookingStatus,
    WeeklySchedule,
    WeeklyBreak,
    BlockedRange,
    TimeSlot,
    SlotStatus,
    utcnow,
)

# MVP constants (later you can move these to core/config.py)
SLOT_MINUTES = 15
HOLD_MINUTES = 10


ACTIVE_BOOKING_STATUSES = (
    BookingStatus.HOLD,
    BookingStatus.PENDING_PAYMENT,
    BookingStatus.CONFIRMED,
)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def expire_holds(db: Session) -> int:
    """
    Expire HELD time_slots and mark related bookings as EXPIRED (if still HOLD/PENDING_PAYMENT).
    """
    now = now_utc()

    slots = db.execute(
        select(TimeSlot).where(
            TimeSlot.status == SlotStatus.HELD,
            TimeSlot.hold_expires_at.is_not(None),
            TimeSlot.hold_expires_at < now,
        )
    ).scalars().all()

    expired = 0
    for s in slots:
        s.status = SlotStatus.FREE
        s.hold_expires_at = None
        s.updated_at = utcnow()
        expired += 1

        # booking might exist; expire it if not already confirmed/cancelled
        if s.booking and s.booking.status in (BookingStatus.HOLD, BookingStatus.PENDING_PAYMENT):
            s.booking.status = BookingStatus.EXPIRED
            s.booking.updated_at = utcnow()

    db.commit()
    return expired


def list_blocks_in_range(db: Session, start_at: datetime, end_at: datetime) -> List[BlockedRange]:
    q = select(BlockedRange).where(and_(BlockedRange.start_at < end_at, BlockedRange.end_at > start_at))
    return db.execute(q).scalars().all()


def get_weekly_schedule_for_weekday(db: Session, weekday: int) -> WeeklySchedule | None:
    return db.execute(select(WeeklySchedule).where(WeeklySchedule.weekday == weekday)).scalar_one_or_none()


def get_weekly_breaks(db: Session, weekday: int) -> List[WeeklyBreak]:
    return db.execute(
        select(WeeklyBreak).where(WeeklyBreak.weekday == weekday).order_by(WeeklyBreak.start_time.asc())
    ).scalars().all()


def ensure_slot_row(db: Session, start_at: datetime) -> TimeSlot:
    """
    Ensures a timeslot row exists for this start_at. If not, create FREE.
    Useful if you compute availability from schedule/breaks and want to create slot row on-demand.
    """
    slot = db.execute(select(TimeSlot).where(TimeSlot.start_at == start_at)).scalar_one_or_none()
    if slot:
        return slot

    now = utcnow()
    slot = TimeSlot(
        start_at=start_at,
        status=SlotStatus.FREE,
        hold_expires_at=None,
        created_at=now,
        updated_at=now,
    )
    db.add(slot)
    try:
        db.commit()
    except Exception:
        db.rollback()
        # Concurrent insert; re-read
        slot = db.execute(select(TimeSlot).where(TimeSlot.start_at == start_at)).scalar_one()

    return slot


def try_hold_slot(db: Session, start_at: datetime) -> TimeSlot | None:
    """
    Transactionally change FREE -> HELD with rowcount=1.
    Assumes start_at is a valid computed available slot (schedule/breaks/blocks checked).
    """
    now = utcnow()
    hold_expires = now + timedelta(minutes=HOLD_MINUTES)

    ensure_slot_row(db, start_at)

    res = db.execute(
        update(TimeSlot)
        .where(TimeSlot.start_at == start_at, TimeSlot.status == SlotStatus.FREE)
        .values(status=SlotStatus.HELD, hold_expires_at=hold_expires, updated_at=utcnow())
    )
    if res.rowcount != 1:
        db.rollback()
        return None

    db.commit()
    return db.execute(select(TimeSlot).where(TimeSlot.start_at == start_at)).scalar_one()


def compute_day_slots(db: Session, day: date) -> List[Tuple[datetime, datetime]]:
    """
    Returns available slots based on schedule - breaks - blocks - held/booked slots.
    Slots are SLOT_MINUTES. Times treated as UTC for MVP.
    """
    weekday = day.weekday()
    schedule = get_weekly_schedule_for_weekday(db, weekday)
    if not schedule or not schedule.enabled:
        return []

    start_dt = datetime.combine(day, schedule.start_time, tzinfo=timezone.utc)
    end_dt = datetime.combine(day, schedule.end_time, tzinfo=timezone.utc)

    slot_delta = timedelta(minutes=SLOT_MINUTES)
    breaks = get_weekly_breaks(db, weekday)
    blocks = list_blocks_in_range(db, start_dt, end_dt)

    existing = db.execute(
        select(TimeSlot).where(
            TimeSlot.start_at >= start_dt,
            TimeSlot.start_at < end_dt,
            TimeSlot.status.in_([SlotStatus.HELD, SlotStatus.BOOKED]),
        )
    ).scalars().all()
    taken = {s.start_at for s in existing}

    def in_break(s: datetime, e: datetime) -> bool:
        for br in breaks:
            br_s = datetime.combine(day, br.start_time, tzinfo=timezone.utc)
            br_e = datetime.combine(day, br.end_time, tzinfo=timezone.utc)
            if br_s < e and br_e > s:
                return True
        return False

    def blocked(s: datetime, e: datetime) -> bool:
        for bl in blocks:
            if bl.start_at < e and bl.end_at > s:
                return True
        return False

    slots: List[Tuple[datetime, datetime]] = []
    cur = start_dt
    while cur + slot_delta <= end_dt:
        s = cur
        e = cur + slot_delta
        if (s not in taken) and (not in_break(s, e)) and (not blocked(s, e)):
            slots.append((s, e))
        cur += slot_delta

    return slots