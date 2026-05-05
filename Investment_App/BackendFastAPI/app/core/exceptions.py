"""
app/core/exceptions.py
──────────────────────
Domain exceptions used across the application.
Routes translate these into appropriate HTTP responses.
"""


class BrokerError(Exception):
    """Base class for all broker-related errors."""

    def __init__(self, broker: str, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.broker = broker
        self.status_code = status_code


class BrokerAuthError(BrokerError):
    """Raised when authentication with the broker fails (401 / 403)."""

    def __init__(self, broker: str, message: str = "Authentication failed") -> None:
        super().__init__(broker, message, status_code=401)


class BrokerNotFoundError(Exception):
    """Raised when a requested broker is not registered."""

    def __init__(self, broker_id: str) -> None:
        super().__init__(f"Broker '{broker_id}' is not registered.")
        self.broker_id = broker_id


class PortfolioError(Exception):
    """Raised when portfolio data cannot be fetched or normalised."""
