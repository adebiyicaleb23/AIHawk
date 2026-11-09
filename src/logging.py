"""
Logging configuration for ApplyPilot - adapted from Auto_Jobs_Applier_AI_Agent
Uses loguru for structured logging.
"""

import sys
from pathlib import Path
from loguru import logger as loguru_logger

from config import (
    LOG_LEVEL,
    LOG_TO_FILE,
    LOG_TO_CONSOLE,
    LOG_FILE_PATH,
    SELENIUM_LOG_FILE_PATH,
)

# Remove default handler
loguru_logger.remove()

# Configure console logging
if LOG_TO_CONSOLE:
    loguru_logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

# Configure file logging
if LOG_TO_FILE:
    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    loguru_logger.add(
        LOG_FILE_PATH,
        level=LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="1 week",
        compression="zip",
    )

# Configure Selenium-specific logging
SELENIUM_LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
selenium_logger = loguru_logger.bind(name="selenium")
loguru_logger.add(
    SELENIUM_LOG_FILE_PATH,
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    rotation="1 day",
    retention="7 days",
    filter=lambda record: record["extra"].get("name") == "selenium",
)

# Export the configured logger
logger = loguru_logger


def get_selenium_logger():
    """Get the selenium-specific logger."""
    return selenium_logger