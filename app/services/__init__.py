"""Business logic. Services take a sqlite3 connection and return plain dicts.

They raise these errors; app/main.py maps them to HTTP status codes.
"""


class NotFoundError(LookupError):
    """The requested user, flight or booking does not exist (HTTP 404)."""


class ConflictError(ValueError):
    """The request is valid but not allowed in the current state (HTTP 409)."""

# Based on IBM's Galaxium Travels demo (https://github.com/IBM/galaxium-travels), Apache License 2.0; cut down and rewritten for Galaxium Lite.
