from __future__ import annotations

from datetime import datetime, time, date, timedelta
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, field_validator


SLOT_MINUTES = 15


def _ensure_tz_aware(dt: datetime) -> datetime:
    # Require timezone-aware datetimes to avoid ambiguity.
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError("datetime must include timezone info (e.g. '2026-03-01T18:00:00Z')")
    return dt


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class WeeklyScheduleItem(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    enabled: bool = True


class WeeklyBreakItem(BaseModel):
    id: Optional[int] = None
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time


class BlockRangeRequest(BaseModel):
    start_at: datetime
    end_at: datetime
    reason: Optional[str] = None

    @field_validator("start_at", "end_at")
    @classmethod
    def tz_aware(cls, v: datetime) -> datetime:
        return _ensure_tz_aware(v)

    @field_validator("end_at")
    @classmethod
    def end_after_start(cls, v: datetime, info):
        start = info.data.get("start_at")
        if start and v <= start:
            raise ValueError("end_at must be after start_at")
        return v


class BookingHoldRequest(BaseModel):
    start_at: datetime
    customer_name: str = Field(min_length=2, max_length=120)
    customer_email: EmailStr
    customer_phone: str = Field(min_length=6, max_length=50)
    description: Optional[str] = Field(default=None, max_length=5000)

    @field_validator("start_at")
    @classmethod
    def tz_aware(cls, v: datetime) -> datetime:
        return _ensure_tz_aware(v)


class BookingPublicResponse(BaseModel):
    id: int
    status: str
    start_at: datetime
    end_at: datetime
    hold_expires_at: Optional[datetime] = None


class CreatePaymentIntentRequest(BaseModel):
    booking_id: int


class CreatePaymentIntentResponse(BaseModel):
    client_secret: str


class AdminBookingListItem(BaseModel):
    id: int
    status: str
    start_at: datetime
    end_at: datetime
    customer_name: str
    customer_email: str
    customer_phone: str
    stripe_payment_intent_id: Optional[str]


class AvailabilitySlot(BaseModel):
    start_at: datetime
    end_at: datetime


class AvailabilityDayResponse(BaseModel):
    day: date
    slots: List[AvailabilitySlot]
