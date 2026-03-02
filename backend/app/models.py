import enum
from datetime import datetime, timezone, time
from typing import Optional

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Enum,
    Boolean,
    Text,
    Time,
    UniqueConstraint,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BookingStatus(str, enum.Enum):
    HOLD = "HOLD"
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class SlotStatus(str, enum.Enum):
    FREE = "FREE"
    HELD = "HELD"
    BOOKED = "BOOKED"


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class WeeklySchedule(Base):
    """
    Weekly availability rule for a weekday:
    weekday: 0=Monday ... 6=Sunday (same convention as Python's datetime.weekday()).
    """
    __tablename__ = "weekly_schedule"
    __table_args__ = (UniqueConstraint("weekday", name="uq_weekly_schedule_weekday"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class WeeklyBreak(Base):
    __tablename__ = "weekly_breaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)


class BlockedRange(Base):
    """
    Blocks a datetime range (UTC). Used to block vacations, appointments, etc.
    """
    __tablename__ = "blocked_ranges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class TimeSlot(Base):
    """
    One row per slot start time (UTC). This is the concurrency guarantee:
    - start_at is unique.
    - status transitions are done transactionally, e.g. FREE -> HELD.
    """
    __tablename__ = "time_slots"
    __table_args__ = (
        UniqueConstraint("start_at", name="uq_time_slots_start_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    status: Mapped[SlotStatus] = mapped_column(
        Enum(SlotStatus, name="slot_status"),
        default=SlotStatus.FREE,
        nullable=False,
    )

    hold_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    booking: Mapped[Optional["Booking"]] = relationship(
        back_populates="time_slot", uselist=False
    )


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Enforce 1 booking per slot at DB level:
    time_slot_id: Mapped[int] = mapped_column(
        ForeignKey("time_slots.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        unique=True,
    )
    time_slot: Mapped[TimeSlot] = relationship(back_populates="booking")

    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    customer_phone: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status"),
        nullable=False,
    )

    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
