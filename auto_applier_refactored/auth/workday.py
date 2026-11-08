"""
Workday Authentication Handler

Handles Workday (myworkdayjobs.com, workday.com) portal authentication
including login, account creation, and multi-step application flows.
"""

import time
import logging
from typing import Optional
from urllib.parse import urlparse

from playwright.sync_api import Page, Frame

from auto_applier_refactored.auth.base import BaseAuthHandler, AuthHandler
from auto_applier_refactored.models import Candidate
from auto_applier_refactored.constants import (
    WORKDAY_SELECTORS,
    POST_CLICK_DELAY,
    AUTH_FORM_DELAY,
    LOGIN_CLICK_DELAY,
    MODAL_OPEN_DELAY,
    PAGE_LOAD_TIMEOUT,
    WORKDAY_MAX_STEPS,
)
from auto_applier_refactored.exceptions import AuthenticationError


class WorkdayAuthHandler(BaseAuthHandler):
    """Handles Workday portal authentication."""

    def can_handle(self, page: Page, url: str) -> bool:
        """Check if this is a Workday portal."""
        return any(domain in url for domain in ("myworkdayjobs.com", "workday.com"))

    def authenticate(self, page: Page, candidate: Candidate) -> bool:
        """
        Handle Workday authentication flow.

        This handles:
        1. Detecting login page vs job page
        2. Clicking "Sign in with email" if needed
        3. Attempting login with existing credentials
        4. Creating account if login fails
        5. Navigating to application form
        """
        self._safe_log("Workday auth detected — attempting login/signup...")

        # Wait for page to fully load
        time.sleep(3)
        page.wait_for_load_state("domcontentloaded", timeout=10000)
        time.sleep(2)

        # Step 1: Click "Sign in with email" if present
        self._click_sign_in_with_email(page)

        # Step 2: Try to sign in first
        if self._try_sign_in(page, candidate):
            self._safe_log("Workday: Signed in successfully!")
            return True

        # Step 3: Try Create Account flow
        if self._try_create_account(page, candidate):
            self._safe_log("Workday: Account creation submitted!")
            return self._verify_past_login(page)

        # Step 4: Check if already past login (e.g., after successful sign in)
        if self._is_on_application_form(page):
            self._safe_log("Workday: Already past login, on application form")
            return True

        # Step 5: Check for form fields indicating application form
        if self._has_application_form_fields(page):
            self._safe_log("Workday: Found application form fields")
            return True

        raise AuthenticationError(
            "Workday authentication failed - could not sign in or create account",
            portal="workday",
            url=page.url
        )

    def is_authenticated(self, page: Page) -> bool:
        """Check if already authenticated (on application form)."""
        return self._is_on_application_form(page) or self._has_application_form_fields(page)

    # -------------------------------------------------------------------------
    # Private Methods
    # -------------------------------------------------------------------------

    def _click_sign_in_with_email(self, page: Page) -> bool:
        """Click 'Sign in with email' button if present."""
        clicked = self._click_first(page, WORKDAY_SELECTORS["sign_in_with_email"], "Sign in with email")
        if clicked:
            self._safe_log("  Clicked 'Sign in with email', waiting for login form...")
            time.sleep(3)
            page.wait_for_load_state("domcontentloaded", timeout=10000)
            time.sleep(2)
        return clicked

    def _try_sign_in(self, page: Page, candidate: Candidate) -> bool:
        """Attempt to sign in with existing credentials."""
        email_inp = page.query_selector(WORKDAY_SELECTORS["email_field"][0])
        if not email_inp or not email_inp.is_visible():
            return False

        email_inp.fill(candidate.email)
        time.sleep(0.5)

        pwd_inp = page.query_selector(WORKDAY_SELECTORS["password_field"][0])
        if not pwd_inp or not pwd_inp.is_visible():
            return False

        pwd_inp.fill(candidate.password)
        time.sleep(0.5)

        if self._click_first(page, WORKDAY_SELECTORS["sign_in_submit"], "Sign In button"):
            time.sleep(4)
            # Check if still on sign-in page (login may have failed)
            still_signin = page.query_selector("[data-automation-id='signInSection']")
            if not still_signin:
                return True
            self._safe_log("Workday: Sign-in failed (no account?). Trying Create Account...")

        return False

    def _try_create_account(self, page: Page, candidate: Candidate) -> bool:
        """Attempt to create a new account."""
        if not self._click_first(page, WORKDAY_SELECTORS["create_account_link"], "Create Account"):
            return False

        time.sleep(3)

        # Fill registration form
        self._fill_field(page, WORKDAY_SELECTORS["email_field"], candidate.email, "email")
        self._fill_field(page, WORKDAY_SELECTORS["password_field"], candidate.password, "password")
        # Confirm password - use same selector as password but look for confirm
        self._fill_field(
            page,
            ["[data-automation-id='verifyPassword'], input[id*='confirm' i], input[name*='confirm' i]"],
            candidate.password,
            "confirm password"
        )
        self._fill_field(
            page,
            ["input[name*='firstName' i], input[id*='firstName' i]"],
            candidate.first_name,
            "first name"
        )
        self._fill_field(
            page,
            ["input[name*='lastName' i], input[id*='lastName' i]"],
            candidate.last_name,
            "last name"
        )

        if self._click_first(page, WORKDAY_SELECTORS["create_account_submit"], "Create Account submit"):
            time.sleep(5)
            return True

        return False

    def _verify_past_login(self, page: Page) -> bool:
        """Verify we're past the login page."""
        time.sleep(3)
        if self._is_on_application_form(page):
            self._safe_log("Workday: Past login, on application form")
            return True

        if self._has_application_form_fields(page):
            self._safe_log("Workday: Found application form fields")
            return True

        return False

    def _is_on_application_form(self, page: Page) -> bool:
        """Check if we're on an actual application form (not just job page)."""
        for selector in WORKDAY_SELECTORS["apply_form_indicators"]:
            el = page.query_selector(selector)
            if el and el.is_visible():
                return True
        return False

    def _has_application_form_fields(self, page: Page) -> bool:
        """Check if page has form fields (more than just search)."""
        form_fields = page.query_selector_all("input[type='text'], input[type='email'], textarea, select")
        return len(form_fields) > 3

    def get_max_steps(self) -> int:
        """Get max steps for Workday multi-step forms."""
        return WORKDAY_MAX_STEPS


def handle_workday_auth(page: Page, candidate: Candidate) -> bool:
    """Convenience function for backward compatibility."""
    handler = WorkdayAuthHandler()
    return handler.authenticate(page, candidate)