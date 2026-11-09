"""
Authenticator for ApplyPilot - adapted from Auto_Jobs_Applier_AI_Agent
Handles LinkedIn authentication with Selenium.
"""

import time
from abc import ABC, abstractmethod
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from src.logging import logger


class AIHawkAuthenticator(ABC):
    """Abstract base class for platform authenticators."""

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)

    @property
    @abstractmethod
    def home_url(self) -> str:
        """Base URL for the platform."""
        pass

    @abstractmethod
    def navigate_to_login(self) -> None:
        """Navigate to the login page."""
        pass

    @property
    @abstractmethod
    def is_logged_in(self) -> bool:
        """Check if user is logged in."""
        pass

    def start(self) -> bool:
        """
        Start the authentication process.

        Returns:
            True if login successful, False otherwise
        """
        logger.info(f"Starting authentication for {self.home_url}")

        # Navigate to home page first
        self.driver.get(self.home_url)
        time.sleep(3)

        # Check if already logged in
        if self.is_logged_in:
            logger.info("Already logged in")
            return True

        # Navigate to login page
        self.navigate_to_login()

        # Wait for manual login
        logger.info("Please log in manually in the browser window...")
        logger.info("Waiting for login to complete (300 seconds timeout)...")

        try:
            # Wait for login to complete by checking logged-in state
            WebDriverWait(self.driver, 300).until(
                lambda d: self.is_logged_in
            )
            logger.info("Login successful!")
            return True
        except TimeoutException:
            logger.error("Login timeout - please try again")
            return False

    def handle_security_checks(self) -> None:
        """Handle any security challenges (2FA, captcha, etc.)."""
        logger.warning("Security checkpoint detected. Please complete the challenge manually.")
        logger.info("Waiting for security check to complete (300 seconds timeout)...")

        try:
            WebDriverWait(self.driver, 300).until(
                lambda d: self.is_logged_in
            )
            logger.info("Security check completed")
        except TimeoutException:
            logger.error("Security check timeout")


class LinkedInAuthenticator(AIHawkAuthenticator):
    """LinkedIn-specific authenticator."""

    @property
    def home_url(self) -> str:
        return "https://www.linkedin.com"

    def navigate_to_login(self) -> None:
        """Navigate to LinkedIn login page."""
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(2)

    @property
    def is_logged_in(self) -> bool:
        """Check if logged into LinkedIn."""
        current_url = self.driver.current_url
        logged_in_indicators = [
            "/feed",
            "/mynetwork",
            "/jobs",
            "/messaging",
            "/notifications",
            "/in/",
        ]
        return any(indicator in current_url for indicator in logged_in_indicators)


def get_authenticator(driver, platform: str) -> AIHawkAuthenticator:
    """
    Factory function to get authenticator for a platform.

    Args:
        driver: Selenium WebDriver
        platform: Platform name (e.g., 'linkedin')

    Returns:
        Authenticator instance

    Raises:
        NotImplementedError: If platform is not supported
    """
    platform = platform.lower()
    if platform == "linkedin":
        return LinkedInAuthenticator(driver)
    else:
        raise NotImplementedError(f"Authenticator for platform '{platform}' not implemented")