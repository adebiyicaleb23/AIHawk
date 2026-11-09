"""
Browser utilities for ApplyPilot - adapted from Auto_Jobs_Applier_AI_Agent
Scrolling and element interaction helpers.
"""

import random
import time
from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from src.logging import logger


def is_scrollable(element: WebElement) -> bool:
    """
    Check if an element has scrollable overflow.

    Args:
        element: Selenium WebElement to check

    Returns:
        True if element is scrollable, False otherwise
    """
    try:
        scroll_height = element.get_attribute("scrollHeight")
        client_height = element.get_attribute("clientHeight")

        if scroll_height and client_height:
            return int(scroll_height) > int(client_height)
    except Exception as e:
        logger.debug(f"Error checking scrollable: {e}")

    return False


def scroll_slow(
    driver: WebDriver,
    scrollable_element: WebElement,
    start: int = 0,
    end: int = 3600,
    step: int = 100,
    reverse: bool = False,
) -> None:
    """
    Perform gradual, human-like scrolling.

    Args:
        driver: Selenium WebDriver
        scrollable_element: Element to scroll
        start: Starting scroll position
        end: Ending scroll position
        step: Initial step size
        reverse: If True, scroll in reverse direction
    """
    try:
        current = start
        step_decrease = 1.0

        if reverse:
            current, end = end, start
            step = -abs(step)
        else:
            step = abs(step)

        # Determine loop condition based on direction
        if not reverse:
            condition = lambda c: c < end
        else:
            condition = lambda c: c > end

        while condition(current):
            # Scroll to current position
            driver.execute_script(
                "arguments[0].scrollTop = arguments[1];",
                scrollable_element,
                current,
            )

            # Randomized delay to mimic human behavior
            delay = random.uniform(0.6, 1.5)
            time.sleep(delay)

            # Decrease step size over time for smooth deceleration
            step = step / step_decrease if step_decrease > 1 else step
            step_decrease += 0.1

            current += step

            # Boundary check
            if not reverse and current >= end:
                current = end
            elif reverse and current <= end:
                current = end

        # Final correction to exact end position
        driver.execute_script(
            "arguments[0].scrollTop = arguments[1];",
            scrollable_element,
            end,
        )

    except Exception as e:
        logger.error(f"Error during slow scroll: {e}")


def scroll_to_bottom(driver: WebDriver, scrollable_element: WebElement, max_scrolls: int = 10) -> None:
    """
    Scroll to bottom of a scrollable element.

    Args:
        driver: Selenium WebDriver
        scrollable_element: Element to scroll
        max_scrolls: Maximum number of scroll attempts
    """
    last_height = 0
    scrolls = 0

    while scrolls < max_scrolls:
        driver.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollHeight;",
            scrollable_element,
        )
        time.sleep(random.uniform(1, 2))

        new_height = driver.execute_script(
            "return arguments[0].scrollHeight;",
            scrollable_element,
        )

        if new_height == last_height:
            break

        last_height = new_height
        scrolls += 1


def wait_for_element(
    driver: WebDriver,
    by: str,
    value: str,
    timeout: int = 10
) -> Optional[WebElement]:
    """
    Wait for an element to be present.

    Args:
        driver: Selenium WebDriver
        by: Locator strategy (e.g., By.ID, By.XPATH)
        value: Locator value
        timeout: Maximum wait time in seconds

    Returns:
        WebElement if found, None otherwise
    """
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException

    try:
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.presence_of_element_located((by, value)))
    except TimeoutException:
        return None


def safe_click(driver: WebDriver, element: WebElement) -> bool:
    """
    Safely click an element using JavaScript.

    Args:
        driver: Selenium WebDriver
        element: Element to click

    Returns:
        True if successful, False otherwise
    """
    try:
        driver.execute_script("arguments[0].click();", element)
        return True
    except Exception as e:
        logger.error(f"Safe click failed: {e}")
        return False