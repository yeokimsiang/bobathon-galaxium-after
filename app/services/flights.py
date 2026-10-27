"""Flight queries."""

import sqlite3

from app.services import NotFoundError


def list_flights(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM flights ORDER BY departure_time, id").fetchall()
    return [dict(row) for row in rows]


def get_flight(conn: sqlite3.Connection, flight_id: int) -> dict:
    row = conn.execute("SELECT * FROM flights WHERE id = ?", (flight_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"Flight {flight_id} not found")
    return dict(row)

# Based on IBM's Galaxium Travels demo (https://github.com/IBM/galaxium-travels), Apache License 2.0; cut down and rewritten for Galaxium Lite.
