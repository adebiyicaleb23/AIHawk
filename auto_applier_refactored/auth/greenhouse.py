"""
Greenhouse Authentication Handler

Greenhouse job boards typically don't require authentication -
applications are direct forms.
"""

import logging
from playwright.sync_api import Page
from auto_applier_refactored.auth.base import BaseAuthHandler, AuthHandler
from auto_applier_refactored.models import Candidate


class GreenhouseAuthHandler(BaseAuthHandler):
    """Handles Greenhouse portal (usually no auth needed)."""

    def can_handle(self, page: Page, url: str) -> bool:
        """Check if this is a Greenhouse portal."""
        return "greenhouse.io" in url or "greenhouse.io" in page.content()[:500]

    def authenticate(self, page: Page, candidate: Candidate) -> bool:
        """Greenhouse forms are usually direct - no auth needed."""
        self._safe_log("Greenhouse portal detected — direct application form")
        return True

    def is_authenticated(self, page: Page) -> bool:
        """Always authenticated for Greenhouse."""
        return True


def handle_greenhouse_auth(page: Page) -> bool:
    """Convenience function for backward compatibility."""
    return True