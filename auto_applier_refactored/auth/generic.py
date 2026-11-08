"""
Generic Authentication Handler

Fallback handler for any portal showing signup/registration forms.
Attempts login first, then account creation.
"""

import time
from playwright.sync_api import Page
from auto_applier_refactored.auth.base import BaseAuthHandler, AuthHandler
from auto_applier_refactored.models import Candidate
from auto_applier_refactored.constants import (
    GENERIC_SELECTORS,
    POST_CLICK_DELAY,
    AUTH_FORM_DELAY,
)
from auto_applier_refactored.exceptions import AuthenticationError


class GenericAuthHandler(BaseAuthHandler):
    """Generic account creation for any portal with signup forms."""

    def can_handle(self, page: Page, url: str) -> bool:
        """Generic handler matches everything (fallback)."""
        return True

    def authenticate(self, page: Page, candidate: Candidate) -> bool:
        """Attempt generic authentication."""
        # First check if there's actually a signup form
        if not self._detect_signup_form(page):
            return True  # No signup form, assume direct application

        self._safe_log("Generic signup form detected — attempting auto-registration...")

        # Try to sign in first with existing credentials
        if self._try_sign_in(page, candidate):
            self._safe_log("Generic portal: Logged in successfully!")
            return True

        # Try Create Account flow
        if self._try_create_account(page, candidate):
            self._safe_log("Generic portal: Account creation submitted!")
            return True

        # Not an error - some portals just don't have auth
        self._safe_log("Generic portal: No auth form handled, continuing...")
        return True

    def is_authenticated(self, page: Page) -> bool:
        """Check if not on a signup form."""
        return not self._detect_signup_form(page)

    # -------------------------------------------------------------------------
    # Private Methods
    # -------------------------------------------------------------------------

    def _detect_signup_form(self, page: Page) -> bool:
        """Detect if page has signup/registration indicators."""
        for sel in GENERIC_SELECTORS["signup_indicators"]:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    return True
            except Exception:
                pass
        return False

    def _try_sign_in(self, page: Page, candidate: Candidate) -> bool:
        """Attempt to sign in with existing credentials."""
        self._fill_field(
            page,
            GENERIC_SELECTORS["email_field"],
            candidate.email,
            "email (login attempt)"
        )
        self._fill_field(
            page,
            GENERIC_SELECTORS["password_field"],
            candidate.password,
            "password (login attempt)"
        )

        if self._click_first(page, GENERIC_SELECTORS["login_button"], "Login button"):
            time.sleep(4)
            # Check if signup form is gone (success)
            if not self._detect_signup_form(page):
                return True
        return False

    def _try_create_account(self, page: Page, candidate: Candidate) -> bool:
        """Attempt to create a new account."""
        if not self._click_first(page, GENERIC_SELECTORS["create_account_button"], "Create Account link"):
            return False

        time.sleep(2)

        # Fill all standard registration fields
        self._fill_field(page, GENERIC_SELECTORS["first_name_field"], candidate.first_name, "first name")
        self._fill_field(page, GENERIC_SELECTORS["last_name_field"], candidate.last_name, "last name")
        self._fill_field(page, GENERIC_SELECTORS["email_field"], candidate.email, "email")
        self._fill_field(page, GENERIC_SELECTORS["password_field"], candidate.password, "password")
        self._fill_field(page, GENERIC_SELECTORS["confirm_password_field"], candidate.password, "confirm password")
        self._fill_field(page, GENERIC_SELECTORS["phone_field"], candidate.phone, "phone")

        # DOB fields
        self._fill_field(page, GENERIC_SELECTORS["dob_field"], candidate.dob, "DOB")
        self._fill_field(page, GENERIC_SELECTORS["dob_day_field"], candidate.dob_day, "DOB day")
        self._fill_field(page, GENERIC_SELECTORS["dob_month_field"], candidate.dob_month, "DOB month")
        self._fill_field(page, GENERIC_SELECTORS["dob_year_field"], candidate.dob_year, "DOB year")

        if self._click_first(page, GENERIC_SELECTORS["register_submit"], "Register submit"):
            time.sleep(5)
            return True

        return False


def handle_generic_signup(page: Page, candidate: Candidate) -> bool:
    """Convenience function for backward compatibility."""
    handler = GenericAuthHandler()
    return handler.authenticate(page, candidate)