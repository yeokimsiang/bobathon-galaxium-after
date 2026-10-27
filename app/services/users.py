"""User queries."""

import sqlite3

from app.services import NotFoundError


def get_user(conn: sqlite3.Connection, user_id: int) -> dict:
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"User {user_id} not found")
    return dict(row)

# Based on IBM's Galaxium Travels demo (https://github.com/IBM/galaxium-travels), Apache License 2.0; cut down and rewritten for Galaxium Lite.
