"""Galaxium Lite: FastAPI routes plus the same API exposed as MCP tools at /mcp."""

import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi_mcp import FastApiMCP

from app import db
from app.schemas import Booking, BookingCreate, Error, Flight, RefundPreview
from app.services import ConflictError, NotFoundError, bookings, flights


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = db.connect()
    try:
        db.init_db(conn)
        db.seed(conn)  # no-op if the database already has data
    finally:
        conn.close()
    yield


app = FastAPI(
    title="Galaxium Lite",
    description="Book interplanetary flights. Swagger UI at /docs, MCP tools at /mcp.",
    version="1.0.0",
    lifespan=lifespan,
)


def get_now() -> datetime:
    """The current UTC time. Tests override this dependency to pin the clock."""
    return db.utc_now()


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


NOT_FOUND = {404: {"model": Error}}
CONFLICT = {409: {"model": Error}}


# Every route needs an explicit operation_id: fastapi-mcp uses it as the MCP tool name.

@app.get("/flights", response_model=list[Flight], tags=["Flights"], operation_id="list_flights")
def list_flights(conn: sqlite3.Connection = Depends(db.get_conn)):
    """List all flights, soonest departure first."""
    return flights.list_flights(conn)


@app.get(
    "/flights/{flight_id}",
    response_model=Flight,
    responses=NOT_FOUND,
    tags=["Flights"],
    operation_id="get_flight",
)
def get_flight(flight_id: int, conn: sqlite3.Connection = Depends(db.get_conn)):
    """Get one flight by id."""
    return flights.get_flight(conn, flight_id)


@app.post(
    "/bookings",
    response_model=Booking,
    status_code=201,
    responses={**NOT_FOUND, **CONFLICT},
    tags=["Bookings"],
    operation_id="book_flight",
)
def book_flight(
    body: BookingCreate,
    conn: sqlite3.Connection = Depends(db.get_conn),
    now: datetime = Depends(get_now),
):
    """Book a seat on a flight for a user."""
    return bookings.create_booking(conn, body.user_id, body.flight_id, now)


@app.get(
    "/users/{user_id}/bookings",
    response_model=list[Booking],
    responses=NOT_FOUND,
    tags=["Bookings"],
    operation_id="list_user_bookings",
)
def list_user_bookings(user_id: int, conn: sqlite3.Connection = Depends(db.get_conn)):
    """List every booking (booked and cancelled) for a user."""
    return bookings.list_user_bookings(conn, user_id)


@app.post(
    "/bookings/{booking_id}/cancel",
    response_model=Booking,
    responses={**NOT_FOUND, **CONFLICT},
    tags=["Bookings"],
    operation_id="cancel_booking",
)
def cancel_booking(
    booking_id: int,
    conn: sqlite3.Connection = Depends(db.get_conn),
    now: datetime = Depends(get_now),
):
    """Cancel a booking. Fails if it is already cancelled or the flight has departed."""
    return bookings.cancel_booking(conn, booking_id, now)


@app.get(
    "/bookings/{booking_id}/refund-preview",
    response_model=RefundPreview,
    responses=NOT_FOUND,
    tags=["Bookings"],
    operation_id="preview_refund",
)
def preview_refund(
    booking_id: int,
    conn: sqlite3.Connection = Depends(db.get_conn),
    now: datetime = Depends(get_now),
):
    """Preview the refund amount for cancelling a booking without actually cancelling it."""
    return bookings.refund_preview(conn, booking_id, now)


# Keep this LAST: FastApiMCP snapshots the routes that exist when it is created,
# so any route defined below this line will not become an MCP tool.
mcp = FastApiMCP(app, name="galaxium-lite")
mcp.mount_http()  # streamable HTTP at /mcp

# Based on IBM's Galaxium Travels demo (https://github.com/IBM/galaxium-travels), Apache License 2.0; cut down and rewritten for Galaxium Lite.
