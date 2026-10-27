"""Pydantic request/response models."""

from typing import Literal

from pydantic import BaseModel, Field

BookingStatus = Literal["booked", "cancelled"]


class Flight(BaseModel):
    id: int
    origin: str
    destination: str
    departure_time: str = Field(description="ISO-8601 UTC, e.g. 2030-01-01T12:00:00Z")
    price: float


class BookingCreate(BaseModel):
    user_id: int
    flight_id: int


class Booking(BaseModel):
    id: int
    user_id: int
    flight_id: int
    status: BookingStatus
    booked_at: str = Field(description="ISO-8601 UTC")


class RefundPreview(BaseModel):
    booking_id: int
    status: BookingStatus
    refund_pct: int
    refund_amount: float


class Error(BaseModel):
    detail: str

# Based on IBM's Galaxium Travels demo (https://github.com/IBM/galaxium-travels), Apache License 2.0; cut down and rewritten for Galaxium Lite.
