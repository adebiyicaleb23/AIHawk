"""
Configuration module for ApplyPilot - adapted from Auto_Jobs_Applier_AI_Agent
"""

import os
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent

# Data folder paths
DATA_FOLDER = PROJECT_ROOT / "data_folder"
DATA_FOLDER_EXAMPLE = PROJECT_ROOT / "data_folder_example"

# Config file names
SECRETS_FILE = "secrets.yaml"
WORK_PREFERENCES_FILE = "work_preferences.yaml"
PLAIN_TEXT_RESUME_FILE = "plain_text_resume.yaml"

# Full paths
SECRETS_PATH = DATA_FOLDER / SECRETS_FILE
WORK_PREFERENCES_PATH = DATA_FOLDER / WORK_PREFERENCES_FILE
PLAIN_TEXT_RESUME_PATH = DATA_FOLDER / PLAIN_TEXT_RESUME_FILE

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_TO_FILE = True
LOG_TO_CONSOLE = True
LOG_FILE_PATH = PROJECT_ROOT / "log" / "app.log"
SELENIUM_LOG_FILE_PATH = PROJECT_ROOT / "log" / "selenium.log"

# Job Application Parameters
JOB_MAX_APPLICATIONS = 10
JOB_MIN_APPLICATIONS = 1
JOB_SUITABILITY_SCORE = 7
MINIMUM_WAIT_TIME_IN_SECONDS = 30

# LLM Configuration
LLM_MODEL_TYPE = os.getenv("LLM_MODEL_TYPE", "openai")  # openai, claude, ollama, gemini, huggingface, perplexity
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_API_URL = os.getenv("LLM_API_URL", "https://api.openai.com/v1")

# Output Directory
JOB_APPLICATIONS_DIR = "job_applications"

# Chrome Profile
CHROME_PROFILE_DIR = PROJECT_ROOT / "chrome_profile" / "linkedin_profile"

# Create directories if they don't exist
DATA_FOLDER.mkdir(exist_ok=True)
(PROJECT_ROOT / "log").mkdir(exist_ok=True)
CHROME_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
(PROJECT_ROOT / JOB_APPLICATIONS_DIR).mkdir(exist_ok=True)

# Selenium Configuration
SELENIUM_IMPLICIT_WAIT = 10
SELENIUM_EXPLICIT_WAIT = 20
SELENIUM_PAGE_LOAD_TIMEOUT = 60