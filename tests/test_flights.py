def test_list_flights_returns_seeded_flights_soonest_first(client):
    response = client.get("/flights")

    assert response.status_code == 200
    flights = response.json()
    assert len(flights) == 6
    departures = [f["departure_time"] for f in flights]
    assert departures == sorted(departures)
    assert flights[0]["destination"] == "Europa"  # departs in 12 hours


def test_get_flight(client):
    response = client.get("/flights/1")

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "origin": "Earth",
        "destination": "Mars",
        "departure_time": "2030-01-11T12:00:00Z",
        "price": 1200.0,
    }


def test_get_unknown_flight_is_404(client):
    response = client.get("/flights/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Flight 999 not found"}

# Based on IBM's Galaxium Travels demo (https://github.com/IBM/galaxium-travels), Apache License 2.0; cut down and rewritten for Galaxium Lite.
