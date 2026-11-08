"""
Lever Authentication Handler

Lever job boards typically don't require authentication -
applications are direct forms.
"""

import logging
from playwright.sync_api import Page
from auto_applier_refactored.auth.base import BaseAuthHandler, AuthHandler
from auto_applier_refactored.models import Candidate


class LeverAuthHandler(BaseAuthHandler):
    """Handles Lever portal (usually no auth needed)."""

    def can_handle(self, page: Page, url: str) -> bool:
        """Check if this is a Lever portal."""
        return "lever.co" in url

    def authenticate(self, page: Page, candidate: Candidate) -> bool:
        """Lever forms are usually direct - no auth needed."""
        self._safe_log("Lever portal detected — direct application form")
        return True

    def is_authenticated(self, page: Page) -> bool:
        """Always authenticated for Lever."""
        return True


def handle_lever_auth(page: Page) -> bool:
    """Convenience function for backward compatibility."""
    return True