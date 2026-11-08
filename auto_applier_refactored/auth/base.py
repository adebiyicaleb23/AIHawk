"""
Authentication Handler Protocol

Abstract base for portal-specific authentication handlers.
"""

from typing import Protocol
from playwright.sync_api import Page

from auto_applier_refactored.models import Candidate


class AuthHandler(Protocol):
    """Protocol for portal authentication handlers."""

    def can_handle(self, page: Page, url: str) -> bool:
        """Check if this handler can handle the given page/URL."""
        ...

    def authenticate(self, page: Page, candidate: Candidate) -> bool:
        """
        Perform authentication on the page.

        Args:
            page: Playwright page object
            candidate: Candidate profile with credentials

        Returns:
            True if authentication succeeded, False otherwise

        Raises:
            AuthenticationError: If authentication fails critically
        """
        ...

    def is_authenticated(self, page: Page) -> bool:
        """Check if already authenticated on the page."""
        ...


class BaseAuthHandler:
    """Base class with common authentication utilities."""

    def __init__(self):
        self.logger = __import__("logging").getLogger(self.__class__.__name__)

    def _fill_field(self, page: Page, selectors: list[str], value: str, label: str = "") -> bool:
        """Try a list of CSS selectors and fill the first visible empty one."""
        for sel in selectors:
            try:
                els = page.query_selector_all(sel)
                for el in els:
                    if el.is_visible() and not el.input_value():
                        el.fill(value)
                        self._safe_log(f"  Filled {label or sel}")
                        return True
            except Exception:
                pass
        return False

    def _click_first(self, page: Page, selectors: list[str], label: str = "", force: bool = False) -> bool:
        """Click the first visible matching element."""
        for sel in selectors:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    self._safe_log(f"  Found and clicking: {label or sel}")
                    try:
                        el.click(force=force, timeout=10000)
                    except Exception:
                        if not force:
                            self._safe_log(f"  Regular click failed, trying force click...")
                            el.click(force=True, timeout=10000)
                    self._safe_log(f"  Clicked: {label or sel}")
                    __import__("time").sleep(2)
                    return True
                elif el:
                    self._safe_log(f"  Found but not visible: {label or sel}")
            except Exception as e:
                self._safe_log(f"  Error clicking {label or sel}: {e}")
                pass
        return False

    def _safe_log(self, msg: str) -> None:
        """Log message with safe ASCII encoding."""
        safe_msg = msg.encode('ascii', 'replace').decode('ascii')
        self.logger.info(safe_msg)

    def _wait_for_load(self, page: Page, timeout: int = 10000) -> None:
        """Wait for page to load."""
        import time
        time.sleep(2)
        page.wait_for_load_state("domcontentloaded", timeout=timeout)
        time.sleep(2)