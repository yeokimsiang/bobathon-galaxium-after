"""Booking lifecycle: create, list, cancel.

Anything that depends on the current time takes an explicit `now` so tests
can pin the clock. Routes pass it in from the `get_now` dependency.
"""

import sqlite3
from datetime import datetime

from app.db import from_iso, to_iso
from app.services import ConflictError, NotFoundError
from app.services.flights import get_flight
from app.services.users import get_user


def get_booking(conn: sqlite3.Connection, booking_id: int) -> dict:
    row = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"Booking {booking_id} not found")
    return dict(row)


def create_booking(conn: sqlite3.Connection, user_id: int, flight_id: int, now: datetime) -> dict:
    get_user(conn, user_id)
    flight = get_flight(conn, flight_id)
    if from_iso(flight["departure_time"]) <= now:
        raise ConflictError(f"Flight {flight_id} has already departed")

    cur = conn.execute(
        "INSERT INTO bookings (user_id, flight_id, status, booked_at) VALUES (?, ?, 'booked', ?)",
        (user_id, flight_id, to_iso(now)),
    )
    conn.commit()
    return get_booking(conn, cur.lastrowid)


def list_user_bookings(conn: sqlite3.Connection, user_id: int) -> list[dict]:
    get_user(conn, user_id)
    rows = conn.execute(
        "SELECT * FROM bookings WHERE user_id = ? ORDER BY id", (user_id,)
    ).fetchall()
    return [dict(row) for row in rows]


def cancel_booking(conn: sqlite3.Connection, booking_id: int, now: datetime) -> dict:
    booking = get_booking(conn, booking_id)
    if booking["status"] == "cancelled":
        raise ConflictError(f"Booking {booking_id} is already cancelled")
    flight = get_flight(conn, booking["flight_id"])
    if from_iso(flight["departure_time"]) <= now:
        raise ConflictError(f"Booking {booking_id} cannot be cancelled after departure")

    conn.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ?", (booking_id,))
    conn.commit()
    return get_booking(conn, booking_id)


def refund_preview(conn: sqlite3.Connection, booking_id: int, now: datetime) -> dict:
    booking = get_booking(conn, booking_id)
    flight = get_flight(conn, booking["flight_id"])

    if booking["status"] == "cancelled":
        pct = 0
    elif from_iso(flight["departure_time"]) <= now:
        raise ConflictError(f"Booking {booking_id} flight has already departed")
    else:
        delta = from_iso(flight["departure_time"]) - now
        seconds = delta.total_seconds()
        if seconds > 7 * 24 * 3600:
            pct = 100
        elif seconds >= 24 * 3600:
            pct = 50
        else:
            pct = 0

    return {
        "booking_id": booking_id,
        "status": booking["status"],
        "refund_pct": pct,
        "refund_amount": round(flight["price"] * pct / 100, 2),
    }

# Based on IBM's Galaxium Travels demo (https://github.com/IBM/galaxium-travels), Apache License 2.0; cut down and rewritten for Galaxium Lite.
