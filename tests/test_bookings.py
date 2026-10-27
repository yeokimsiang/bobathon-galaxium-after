from datetime import timedelta

import pytest

from app.services import ConflictError, bookings
from tests.conftest import NOW


def test_book_flight(client):
    response = client.post("/bookings", json={"user_id": 2, "flight_id": 5})

    assert response.status_code == 201
    body = response.json()
    assert body["user_id"] == 2
    assert body["flight_id"] == 5
    assert body["status"] == "booked"
    assert body["booked_at"] == "2030-01-01T12:00:00Z"


@pytest.mark.parametrize(
    ("payload", "detail"),
    [
        ({"user_id": 999, "flight_id": 1}, "User 999 not found"),
        ({"user_id": 1, "flight_id": 999}, "Flight 999 not found"),
    ],
)
def test_book_flight_unknown_user_or_flight_is_404(client, payload, detail):
    response = client.post("/bookings", json=payload)

    assert response.status_code == 404
    assert response.json() == {"detail": detail}


def test_list_user_bookings(client):
    response = client.get("/users/1/bookings")

    assert response.status_code == 200
    assert [b["id"] for b in response.json()] == [1, 2]


def test_list_bookings_for_unknown_user_is_404(client):
    assert client.get("/users/999/bookings").status_code == 404


def test_cancel_booking(client):
    response = client.post("/bookings/1/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    statuses = {b["id"]: b["status"] for b in client.get("/users/1/bookings").json()}
    assert statuses == {1: "cancelled", 2: "booked"}


def test_cancel_already_cancelled_booking_is_409(client):
    response = client.post("/bookings/4/cancel")

    assert response.status_code == 409
    assert response.json() == {"detail": "Booking 4 is already cancelled"}


def test_cannot_cancel_after_departure(conn):
    after_departure = NOW + timedelta(hours=13)  # booking 3 departs NOW + 12h

    with pytest.raises(ConflictError, match="after departure"):
        bookings.cancel_booking(conn, 3, now=after_departure)


def test_refund_preview_100pct(client):
    response = client.get("/bookings/1/refund-preview")

    assert response.status_code == 200
    body = response.json()
    assert body["booking_id"] == 1
    assert body["status"] == "booked"
    assert body["refund_pct"] == 100
    assert body["refund_amount"] == 1200.0


def test_refund_preview_50pct(client):
    response = client.get("/bookings/2/refund-preview")

    assert response.status_code == 200
    body = response.json()
    assert body["booking_id"] == 2
    assert body["status"] == "booked"
    assert body["refund_pct"] == 50
    assert body["refund_amount"] == 150.0


def test_refund_preview_0pct_under_24h(client):
    response = client.get("/bookings/3/refund-preview")

    assert response.status_code == 200
    body = response.json()
    assert body["booking_id"] == 3
    assert body["status"] == "booked"
    assert body["refund_pct"] == 0
    assert body["refund_amount"] == 0.0


def test_refund_preview_0pct_already_cancelled(client):
    response = client.get("/bookings/4/refund-preview")

    assert response.status_code == 200
    body = response.json()
    assert body["booking_id"] == 4
    assert body["status"] == "cancelled"
    assert body["refund_pct"] == 0
    assert body["refund_amount"] == 0.0


def test_refund_preview_unknown_booking_is_404(client):
    assert client.get("/bookings/999/refund-preview").status_code == 404


def test_refund_preview_after_departure_is_409(conn):
    after_departure = NOW + timedelta(hours=13)  # booking 3 departs NOW + 12h

    with pytest.raises(ConflictError, match="already departed"):
        bookings.refund_preview(conn, 3, now=after_departure)

# Based on IBM's Galaxium Travels demo (https://github.com/IBM/galaxium-travels), Apache License 2.0; cut down and rewritten for Galaxium Lite.
