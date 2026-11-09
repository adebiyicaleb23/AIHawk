"""
Time utilities for ApplyPilot - adapted from Auto_Jobs_Applier_AI_Agent
Random sleep functions for human-like behavior.
"""

import random
import time


def short_sleep() -> None:
    """Sleep for a short random duration (1.2-3 seconds)."""
    time.sleep(random.uniform(1.2, 3))


def medium_sleep() -> None:
    """Sleep for a medium random duration (3-5 seconds)."""
    time.sleep(random.uniform(3, 5))


def long_sleep() -> None:
    """Sleep for a long random duration (5-10 seconds)."""
    time.sleep(random.uniform(5, 10))


def random_sleep(min_seconds: float = 1, max_seconds: float = 3) -> None:
    """Sleep for a random duration within the given range."""
    time.sleep(random.uniform(min_seconds, max_seconds))