"""
Chrome utilities for ApplyPilot - adapted from Auto_Jobs_Applier_AI_Agent
Configures Chrome browser with persistent profile for LinkedIn.
"""

from pathlib import Path
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config import CHROME_PROFILE_DIR


def get_chrome_options(headless: bool = False) -> Options:
    """
    Configure Chrome options with persistent profile.

    Args:
        headless: Whether to run in headless mode

    Returns:
        Configured ChromeOptions
    """
    options = Options()

    # Create profile directory if it doesn't exist
    CHROME_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    # Use persistent profile for LinkedIn login persistence
    options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR.parent}")
    options.add_argument(f"--profile-directory={CHROME_PROFILE_DIR.name}")

    # Performance options
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-cache")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")  # Faster loading
    options.add_argument("--disable-stylesheets")  # Faster loading

    # Anti-detection options
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Window size
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")

    # Headless mode
    if headless:
        options.add_argument("--headless=new")

    # Preferences to disable images and stylesheets
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
    }
    options.add_experimental_option("prefs", prefs)

    return options


def get_chrome_driver(headless: bool = False):
    """
    Create and return a configured Chrome WebDriver.

    Args:
        headless: Whether to run in headless mode

    Returns:
        Configured Chrome WebDriver instance
    """
    from selenium import webdriver

    options = get_chrome_options(headless)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Execute CDP commands to avoid detection
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
    })

    return driver