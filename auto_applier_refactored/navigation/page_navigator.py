"""
Page Navigator

Handles page navigation, iframe switching, and form detection for job applications.
"""

import time
import logging
from typing import Optional
from playwright.sync_api import Page, Frame

from auto_applier_refactored.constants import (
    WORKDAY_SELECTORS,
    GENERIC_SELECTORS,
    POST_CLICK_DELAY,
    POST_APPLY_CLICK_DELAY,
    INITIAL_PAGE_LOAD_DELAY,
    MODAL_OPEN_DELAY,
    IFRAME_LOAD_TIMEOUT,
    MODAL_WAIT_TIMEOUT,
    FORM_WAIT_TIMEOUT,
)
from auto_applier_refactored.navigation.apply_button_finder import find_and_click_apply
from auto_applier_refactored.exceptions import NavigationError


logger = logging.getLogger(__name__)


class PageNavigator:
    """Handles page navigation and form detection for job applications."""

    def __init__(self, page: Page):
        self.page = page
        self._iframe_switched = False

    def goto_and_wait(self, url: str, timeout: int = 50000) -> None:
        """Navigate to URL and wait for load."""
        self.page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        time.sleep(INITIAL_PAGE_LOAD_DELAY)

    def click_apply_button(self) -> bool:
        """Find and click the apply button."""
        return find_and_click_apply(self.page)

    def wait_for_form(self, min_fields: int = 3, timeout: int = FORM_WAIT_TIMEOUT) -> bool:
        """Wait for application form to appear."""
        start_time = time.time()
        while time.time() - start_time < timeout / 1000:
            form_elements = self.page.query_selector_all(
                "input[data-automation-id='firstName'], "
                "input[data-automation-id='lastName'], "
                "input[name*='firstName' i], "
                "input[name*='lastName' i], "
                "input[type='file'], "
                "textarea"
            )
            if len(form_elements) >= min_fields:
                self._safe_log(f"  Form detected ({len(form_elements)} fields)")
                return True
            time.sleep(1)
        return False

    def handle_post_apply_navigation(self) -> None:
        """Handle navigation after clicking apply button."""
        time.sleep(POST_APPLY_CLICK_DELAY)
        self._safe_log(f"  After Apply click, URL: {self.page.url}")

        # Check for modal/dialog
        self._handle_modal_iframe()

        # If no iframe switched, check main page iframes (Workday)
        if not self._iframe_switched and self._is_workday():
            self._check_main_page_iframes()

        # Handle LinkedIn manual apply bypass
        self._handle_linkedin_bypass()

        # Check if form appeared on same page
        self._check_for_form()

        # Try direct apply URL for Workday if still no form
        if self._is_workday() and not self._has_form():
            self._try_direct_apply_urls()

    def _handle_modal_iframe(self) -> None:
        """Check for and switch to modal iframe."""
        modal = self.page.query_selector(
            "[role='dialog'], [data-automation-id='modal'], .modal, .workday-modal"
        )
        if not modal:
            return

        self._safe_log("  Modal/dialog detected after Apply click")
        try:
            self.page.wait_for_selector(
                "[role='dialog'], [data-automation-id='modal'], .modal",
                timeout=MODAL_WAIT_TIMEOUT
            )
        except Exception:
            pass
        time.sleep(MODAL_OPEN_DELAY)

        # Look for iframes INSIDE the modal
        modal_iframes = modal.query_selector_all("iframe")
        for iframe in modal_iframes:
            if self._try_switch_to_iframe(iframe):
                return

    def _check_main_page_iframes(self) -> None:
        """Check for application iframes on main page (Workday)."""
        self._safe_log("  Checking for Workday iframes on main page...")

        for attempt in range(5):
            iframes = self.page.query_selector_all("iframe")
            for iframe in iframes:
                if self._try_switch_to_iframe(iframe, check_keywords=True):
                    return
            if self._iframe_switched:
                break
            time.sleep(2)

    def _try_switch_to_iframe(self, iframe, check_keywords: bool = False) -> bool:
        """Try to switch to an iframe if it contains application form."""
        try:
            src = iframe.get_attribute("src") or ""
            if check_keywords:
                if not any(kw in src.lower() for kw in
                          ["apply", "candidate", "job", "linkedin", "gadget"]):
                    return False

            self._safe_log(f"  Found potential application iframe: {src[:100]}")
            frame = iframe.content_frame()
            if not frame:
                return False

            time.sleep(2)
            form_check = frame.query_selector_all("input, textarea, select")
            self._safe_log(f"  Iframe has {len(form_check)} form elements")

            if len(form_check) > 3:
                self._safe_log(f"  Switching to iframe with {len(form_check)} form elements")
                self.page = frame
                self._iframe_switched = True
                return True

            # Even if not many form elements yet, try waiting more
            time.sleep(3)
            form_check = frame.query_selector_all("input, textarea, select")
            if len(form_check) > 0:
                self._safe_log(f"  Switching to iframe (delayed load) with {len(form_check)} form elements")
                self.page = frame
                self._iframe_switched = True
                return True

        except Exception as e:
            self._safe_log(f"  Error checking iframe: {e}")
        return False

    def _handle_linkedin_bypass(self) -> None:
        """Handle LinkedIn 'Continue manually' bypass."""
        modal = self.page.query_selector(
            "[role='dialog'], [data-automation-id='modal'], .modal, .workday-modal"
        )
        if not modal:
            return

        manual_selectors = [
            "button:has-text('Continue manually')",
            "button:has-text('Apply manually')",
            "button:has-text('Skip')",
            "button:has-text('Continue without LinkedIn')",
            "a:has-text('Continue manually')",
            "a:has-text('Apply manually')",
            "[data-automation-id*='manual' i]",
        ]

        for sel in manual_selectors:
            try:
                el = self.page.query_selector(sel)
                if el and el.is_visible():
                    el.click(force=True, timeout=10000)
                    self._safe_log("  Clicked manual apply bypass")
                    self.page.wait_for_load_state("domcontentloaded", timeout=30000)
                    time.sleep(5)
                    self._safe_log(f"  After manual bypass, URL: {self.page.url}")
                    return
            except Exception:
                pass

    def _check_for_form(self) -> bool:
        """Check if form elements appeared on current page."""
        form_elements = self.page.query_selector_all(
            "input[data-automation-id='firstName'], "
            "input[data-automation-id='lastName'], "
            "input[name*='firstName' i], "
            "input[name*='lastName' i], "
            "input[type='file'], "
            "textarea"
        )
        if len(form_elements) > 2:
            self._safe_log(f"  Form detected ({len(form_elements)} fields)")
            return True
        return False

    def _has_form(self) -> bool:
        """Check if current page has form (without logging)."""
        form_elements = self.page.query_selector_all(
            "input[data-automation-id='firstName'], "
            "input[name*='firstName' i], "
            "input[type='file'], "
            "textarea"
        )
        return len(form_elements) > 2

    def _try_direct_apply_urls(self) -> None:
        """Try direct apply URL patterns for Workday."""
        from auto_applier_refactored.navigation.url_resolver import build_workday_apply_urls

        self._safe_log("  No form detected, trying direct apply URLs...")
        apply_urls = build_workday_apply_urls(self.page.url)

        for apply_url in apply_urls:
            self._safe_log(f"  Trying direct apply URL: {apply_url}")
            self.page.goto(apply_url, timeout=30000, wait_until="domcontentloaded")
            time.sleep(3)
            if self._has_form():
                self._safe_log(f"  Form found at apply URL!")
                return

    def _is_workday(self) -> bool:
        """Check if current page is Workday."""
        from auto_applier_refactored.navigation.url_resolver import is_workday_url
        return is_workday_url(self.page.url)

    def handle_cookie_consent(self) -> None:
        """Handle cookie/privacy consent modals."""
        for sel in WORKDAY_SELECTORS["cookie_consent"]:
            try:
                el = self.page.query_selector(sel)
                if el and el.is_visible():
                    el.click(force=True, timeout=5000)
                    self._safe_log(f"  Handled cookie consent: {sel}")
                    time.sleep(1)
                    return
            except Exception:
                pass

    def click_submit(self) -> bool:
        """Click submit button."""
        return self._click_first(WORKDAY_SELECTORS["submit_button"], "Submit")

    def click_next(self) -> bool:
        """Click next/continue button."""
        return self._click_first(WORKDAY_SELECTORS["next_continue_button"], "Next/Continue")

    def _click_first(self, selectors: list, label: str) -> bool:
        """Click first visible matching element."""
        for sel in selectors:
            try:
                el = self.page.query_selector(sel)
                if el and el.is_visible():
                    self._safe_log(f"  Clicking {label}: {sel}")
                    el.click(force=True, timeout=10000)
                    time.sleep(3)
                    return True
            except Exception as e:
                self._safe_log(f"  Error clicking {label} ({sel}): {e}")
        return False

    def get_max_steps(self) -> int:
        """Get max steps for multi-step form."""
        from auto_applier_refactored.constants import WORKDAY_MAX_STEPS, DEFAULT_MAX_STEPS
        return WORKDAY_MAX_STEPS if self._is_workday() else DEFAULT_MAX_STEPS

    def _safe_log(self, msg: str) -> None:
        """Log message with safe ASCII encoding."""
        safe_msg = msg.encode('ascii', 'replace').decode('ascii')
        logger.info(safe_msg)


# Backward compatibility
def handle_cookie_consent(page: Page) -> None:
    """Handle cookie/privacy consent modals."""
    navigator = PageNavigator(page)
    navigator.handle_cookie_consent()