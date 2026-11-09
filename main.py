#!/usr/bin/env python3
"""
ApplyPilot - Automated Job Application System
Entry point adapted from Auto_Jobs_Applier_AI_Agent
"""

import os
import sys
import yaml
import click
from pathlib import Path

from config import (
    DATA_FOLDER,
    SECRETS_PATH,
    WORK_PREFERENCES_PATH,
    PLAIN_TEXT_RESUME_PATH,
    JOB_APPLICATIONS_DIR,
)
from src.logging import logger
from src.job_application_profile import JobApplicationProfile
from src.ai_hawk.bot_facade import AIHawkBotFacade
from src.utils.chrome_utils import get_chrome_driver


class ConfigValidator:
    """Validates configuration files."""

    @staticmethod
    def validate_secrets(secrets_path: Path) -> dict:
        """Validate secrets.yaml file."""
        if not secrets_path.exists():
            raise FileNotFoundError(f"Secrets file not found: {secrets_path}")

        with open(secrets_path, 'r', encoding='utf-8') as f:
            secrets = yaml.safe_load(f) or {}

        if not secrets.get('llm_api_key'):
            raise ValueError("LLM API key not found in secrets.yaml")

        return secrets

    @staticmethod
    def validate_work_preferences(work_prefs_path: Path) -> dict:
        """Validate work_preferences.yaml file."""
        if not work_prefs_path.exists():
            raise FileNotFoundError(f"Work preferences file not found: {work_prefs_path}")

        with open(work_prefs_path, 'r', encoding='utf-8') as f:
            prefs = yaml.safe_load(f) or {}

        required_sections = ['positions', 'locations', 'experience_level', 'job_types', 'date']
        for section in required_sections:
            if section not in prefs:
                raise ValueError(f"Missing required section in work_preferences.yaml: {section}")

        return prefs

    @staticmethod
    def validate_resume(resume_path: Path) -> str:
        """Validate and load plain_text_resume.yaml file."""
        if not resume_path.exists():
            raise FileNotFoundError(f"Resume file not found: {resume_path}")

        with open(resume_path, 'r', encoding='utf-8') as f:
            resume_content = f.read()

        if not resume_content.strip():
            raise ValueError("Resume file is empty")

        return resume_content


class FileManager:
    """Manages file operations."""

    @staticmethod
    def ensure_directories() -> None:
        """Ensure all required directories exist."""
        DATA_FOLDER.mkdir(parents=True, exist_ok=True)
        Path(JOB_APPLICATIONS_DIR).mkdir(parents=True, exist_ok=True)
        Path("log").mkdir(parents=True, exist_ok=True)
        Path("data_folder/output").mkdir(parents=True, exist_ok=True)

    @staticmethod
    def check_config_files() -> bool:
        """Check if all required config files exist."""
        required_files = [
            (SECRETS_PATH, "secrets.yaml"),
            (WORK_PREFERENCES_PATH, "work_preferences.yaml"),
            (PLAIN_TEXT_RESUME_PATH, "plain_text_resume.yaml"),
        ]

        missing = []
        for path, name in required_files:
            if not path.exists():
                missing.append(name)

        if missing:
            logger.error(f"Missing config files: {', '.join(missing)}")
            logger.error(f"Please create them in {DATA_FOLDER}/")
            return False

        return True


def create_and_run_bot(
    resume_path: str = None,
    collect_only: bool = False,
    headless: bool = False
) -> None:
    """
    Create and run the job application bot.

    Args:
        resume_path: Optional path to PDF resume
        collect_only: If True, only collect job data without applying
        headless: Run browser in headless mode
    """
    logger.info("Starting ApplyPilot...")

    # Validate configuration
    try:
        secrets = ConfigValidator.validate_secrets(SECRETS_PATH)
        work_preferences = ConfigValidator.validate_work_preferences(WORK_PREFERENCES_PATH)
        resume_content = ConfigValidator.validate_resume(PLAIN_TEXT_RESUME_PATH)
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        sys.exit(1)

    # Load resume profile
    try:
        profile = JobApplicationProfile(resume_content)
        logger.info(f"Loaded profile for: {profile.personal_information.get('full_name', 'Unknown')}")
    except Exception as e:
        logger.error(f"Failed to load resume profile: {e}")
        sys.exit(1)

    # Initialize browser
    logger.info("Initializing browser...")
    driver = get_chrome_driver(headless=headless)

    try:
        # Create bot facade
        bot = AIHawkBotFacade()

        # Set credentials (from environment or prompt)
        linkedin_email = os.getenv("LINKEDIN_EMAIL")
        linkedin_password = os.getenv("LINKEDIN_PASSWORD")

        if not linkedin_email or not linkedin_password:
            logger.info("LinkedIn credentials not found in environment.")
            linkedin_email = input("Enter LinkedIn email: ").strip()
            linkedin_password = input("Enter LinkedIn password: ").strip()

        if not linkedin_email or not linkedin_password:
            logger.error("LinkedIn credentials are required")
            sys.exit(1)

        bot.set_credentials(linkedin_email, linkedin_password)

        # Set API key
        api_key = secrets.get('llm_api_key')
        if not api_key:
            logger.error("LLM API key not found in secrets.yaml")
            sys.exit(1)
        bot.set_api_key(api_key)

        # Set job application profile and resume
        resume_file = resume_path or profile.personal_information.get('resume_path', '')
        bot.set_job_application_profile_and_resume(profile, resume_file)

        # Initialize LLM answerer
        from src.ai_hawk.llm.llm_manager import AIAdapter, GPTAnswerer
        llm_model = AIAdapter.get_model()
        gpt_answerer = GPTAnswerer(llm_model)
        bot.set_gpt_answerer_and_resume_generator(gpt_answerer, None)

        # Set parameters
        parameters = {
            'positions': work_preferences.get('positions', []),
            'locations': work_preferences.get('locations', []),
            'company_blacklist': work_preferences.get('company_blacklist', []),
            'title_blacklist': work_preferences.get('title_blacklist', []),
            'location_blacklist': work_preferences.get('location_blacklist', []),
            'apply_once_at_company': work_preferences.get('apply_once_at_company', True),
            'distance': work_preferences.get('distance', 0),
            'uploads': {'resume': resume_file},
            'outputFileDirectory': JOB_APPLICATIONS_DIR,
            'experience_level': work_preferences.get('experience_level', {}),
            'job_types': work_preferences.get('job_types', {}),
            'date': work_preferences.get('date', {}),
            'remote': work_preferences.get('remote', True),
            'hybrid': work_preferences.get('hybrid', True),
            'onsite': work_preferences.get('onsite', False),
        }
        bot.set_parameters(parameters)

        # Start login
        logger.info("Starting LinkedIn login...")
        if not bot.start_login():
            logger.error("Login failed")
            sys.exit(1)

        # Run collection or application
        if collect_only:
            logger.info("Starting job data collection...")
            bot.start_collect_data()
        else:
            logger.info("Starting job application process...")
            bot.start_apply()

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}", exc_info=True)
    finally:
        driver.quit()
        logger.info("Browser closed")


@click.command()
@click.option(
    '--resume',
    type=click.Path(exists=True),
    help='Path to PDF resume file'
)
@click.option(
    '--collect',
    is_flag=True,
    help='Only collect job data, do not apply'
)
@click.option(
    '--headless',
    is_flag=True,
    help='Run browser in headless mode'
)
def main(resume: str, collect: bool, headless: bool) -> None:
    """
    ApplyPilot - Automated Job Application System

    Examples:
        python main.py                    # Run with dynamic resume generation
        python main.py --resume resume.pdf  # Use specific PDF resume
        python main.py --collect          # Collect job data only
        python main.py --headless         # Run in headless mode
    """
    # Ensure directories exist
    FileManager.ensure_directories()

    # Check config files
    if not FileManager.check_config_files():
        logger.error("Please run setup first or create config files in data_folder/")
        sys.exit(1)

    # Run bot
    create_and_run_bot(
        resume_path=resume,
        collect_only=collect,
        headless=headless
    )


if __name__ == "__main__":
    main()