"""
Apply Button Finder

Finds and clicks the Apply button on job pages.
"""

import logging
from playwright.sync_api import Page

from auto_applier_refactored.constants import WORKDAY_SELECTORS
from auto_applier_refactored.navigation.url_resolver import is_workday_url


logger = logging.getLogger(__name__)


APPLY_BUTTON_SELECTORS = [
    "button:has-text('Apply')",
    "a:has-text('Apply')",
    "button:has-text('Easy Apply')",
    "a:has-text('Easy Apply')",
    "[data-automation-id='applyButton']",
    "button:has-text('Apply Now')",
    "a:has-text('Apply Now')",
    "a:has-text('Apply with Resume')",
]


def find_and_click_apply(page: Page) -> bool:
    """
    Find and click the Apply button on the page.

    Args:
        page: Playwright page object

    Returns:
        True if button was clicked, False otherwise
    """
    # First, let's see what apply-related elements exist
    apply_elements = page.query_selector_all(
        "button:has-text('Apply'), a:has-text('Apply'), "
        "[data-automation-id='applyButton'], "
        "button:has-text('Apply Now'), a:has-text('Apply Now'), "
        "a:has-text('Apply with Resume')"
    )
    _safe_log(f"  Found {len(apply_elements)} apply-related elements on page")

    # Try standard selectors
    clicked = _click_first(page, APPLY_BUTTON_SELECTORS, "Apply button")

    # If no Apply button found on Workday job page, try clicking "Sign In" first
    # Many Workday portals require sign-in before showing Apply button
    if not clicked and is_workday_url(page.url):
        _safe_log("  No Apply button found on Workday job page, trying Sign In...")
        sign_in_clicked = _click_first(page, WORKDAY_SELECTORS["sign_in_link"], "Sign In link")
        if sign_in_clicked:
            _safe_log("  Clicked Sign In, waiting for login page/modal...")
            import time
            time.sleep(5)
            # Check if a modal opened
            modal = page.query_selector(
                "[role='dialog'], [data-automation-id='modal'], .modal, .workday-modal"
            )
            if modal:
                _safe_log("  Modal opened after Sign In click")
                try:
                    page.wait_for_selector(
                        "[role='dialog'], [data-automation-id='modal'], .modal",
                        timeout=10000
                    )
                except Exception:
                    pass
                import time
                time.sleep(2)
            # After sign in, try Apply button again
            clicked = _click_first(page, APPLY_BUTTON_SELECTORS, "Apply button (after sign in)")

    return clicked


def _click_first(page: Page, selectors: list, label: str) -> bool:
    """Click first visible matching element."""
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                _safe_log(f"  Found and clicking: {label} ({sel})")
                try:
                    el.click(force=True, timeout=10000)
                except Exception:
                    pass  # force=True already tried
                import time
                time.sleep(2)
                return True
        except Exception:
            pass
    return False


def _safe_log(msg: str) -> None:
    """Log message with safe ASCII encoding."""
    safe_msg = msg.encode('ascii', 'replace').decode('ascii')
    logger.info(safe_msg)