"""Authentication handlers for different job portals."""

from auto_applier_refactored.auth.base import AuthHandler
from auto_applier_refactored.auth.workday import WorkdayAuthHandler
from auto_applier_refactored.auth.greenhouse import GreenhouseAuthHandler
from auto_applier_refactored.auth.lever import LeverAuthHandler
from auto_applier_refactored.auth.generic import GenericAuthHandler

AUTH_HANDLERS = [
    WorkdayAuthHandler(),
    GreenhouseAuthHandler(),
    LeverAuthHandler(),
    GenericAuthHandler(),  # Fallback - must be last
]

def get_auth_handler(page, url: str) -> AuthHandler:
    """Get the appropriate auth handler for the current page/URL."""
    for handler in AUTH_HANDLERS:
        if handler.can_handle(page, url):
            return handler
    return GenericAuthHandler()

__all__ = [
    "AuthHandler",
    "WorkdayAuthHandler",
    "GreenhouseAuthHandler",
    "LeverAuthHandler",
    "GenericAuthHandler",
    "get_auth_handler",
    "AUTH_HANDLERS",
]