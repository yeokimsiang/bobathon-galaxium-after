"""SQLite schema, connections and demo seed data (stdlib sqlite3, no ORM)."""

import os
import sqlite3
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

# Read at call time so tests can point the app at a temporary file.
DEFAULT_DB_PATH = "galaxium.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id    INTEGER PRIMARY KEY,
    name  TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS flights (
    id             INTEGER PRIMARY KEY,
    origin         TEXT NOT NULL,
    destination    TEXT NOT NULL,
    departure_time TEXT NOT NULL,  -- ISO-8601 UTC, e.g. 2030-01-01T12:00:00Z
    price          REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS bookings (
    id        INTEGER PRIMARY KEY,
    user_id   INTEGER NOT NULL REFERENCES users(id),
    flight_id INTEGER NOT NULL REFERENCES flights(id),
    status    TEXT NOT NULL CHECK (status IN ('booked', 'cancelled')),
    booked_at TEXT NOT NULL        -- ISO-8601 UTC
);
"""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(moment: datetime) -> str:
    """Format a datetime as ISO-8601 UTC with a trailing Z."""
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def db_path() -> str:
    return os.environ.get("GALAXIUM_DB", DEFAULT_DB_PATH)


def connect(path: str | None = None) -> sqlite3.Connection:
    # check_same_thread=False: FastAPI may run a sync dependency and the route
    # that uses it on different worker threads.
    conn = sqlite3.connect(path or db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_conn() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency: one connection per request."""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def seed(conn: sqlite3.Connection, now: datetime | None = None) -> bool:
    """Insert demo data relative to `now`. Does nothing if users already exist.

    Departure times are relative to seed time so every refund tier can be
    demonstrated: booking 1 departs in ~10 days, booking 2 in ~3 days,
    booking 3 in ~12 hours, and booking 4 is already cancelled.
    """
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
        return False
    now = (now or utc_now()).replace(microsecond=0)

    conn.executemany(
        "INSERT INTO users (id, name, email) VALUES (?, ?, ?)",
        [
            (1, "Sally Ride", "sally@galaxium.example"),
            (2, "Yuri Gagarin", "yuri@galaxium.example"),
            (3, "Valentina Tereshkova", "valentina@galaxium.example"),
        ],
    )
    conn.executemany(
        "INSERT INTO flights (id, origin, destination, departure_time, price) VALUES (?, ?, ?, ?, ?)",
        [
            (1, "Earth", "Mars", to_iso(now + timedelta(days=10)), 1200.0),
            (2, "Earth", "Moon", to_iso(now + timedelta(days=3)), 300.0),
            (3, "Mars", "Europa", to_iso(now + timedelta(hours=12)), 2500.0),
            (4, "Moon", "Earth", to_iso(now + timedelta(days=5)), 280.0),
            (5, "Earth", "Titan", to_iso(now + timedelta(days=30)), 4000.0),
            (6, "Venus", "Earth", to_iso(now + timedelta(days=20)), 950.0),
        ],
    )
    booked_at = to_iso(now - timedelta(days=1))
    conn.executemany(
        "INSERT INTO bookings (id, user_id, flight_id, status, booked_at) VALUES (?, ?, ?, ?, ?)",
        [
            (1, 1, 1, "booked", booked_at),
            (2, 1, 2, "booked", booked_at),
            (3, 2, 3, "booked", booked_at),
            (4, 3, 4, "cancelled", booked_at),
        ],
    )
    conn.commit()
    return True

# Based on IBM's Galaxium Travels demo (https://github.com/IBM/galaxium-travels), Apache License 2.0; cut down and rewritten for Galaxium Lite.
