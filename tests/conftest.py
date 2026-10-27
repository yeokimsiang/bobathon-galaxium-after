from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app, get_now

# A fixed clock. Seed data is laid out relative to this, so tests never drift.
NOW = datetime(2030, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def db_file(tmp_path, monkeypatch):
    """A fresh, seeded SQLite file per test. The real galaxium.db is never touched."""
    path = tmp_path / "test.db"
    monkeypatch.setenv("GALAXIUM_DB", str(path))
    conn = db.connect()
    db.init_db(conn)
    db.seed(conn, now=NOW)
    conn.close()
    return path


@pytest.fixture
def conn(db_file):
    connection = db.connect()
    yield connection
    connection.close()


@pytest.fixture
def client(db_file):
    app.dependency_overrides[get_now] = lambda: NOW
    # No `with` block: the lifespan would seed using the real clock.
    yield TestClient(app)
    app.dependency_overrides.clear()

# Based on IBM's Galaxium Travels demo (https://github.com/IBM/galaxium-travels), Apache License 2.0; cut down and rewritten for Galaxium Lite.
