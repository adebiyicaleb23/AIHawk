"""
Job Manager for ApplyPilot - adapted from Auto_Jobs_Applier_AI_Agent
Handles job searching, filtering, and application orchestration.
"""

import json
import os
import random
import time
import traceback
from itertools import product
from pathlib import Path
from typing import List, Optional

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

import urllib.parse
import re

from config import (
    JOB_MAX_APPLICATIONS,
    JOB_MIN_APPLICATIONS,
    MINIMUM_WAIT_TIME_IN_SECONDS,
)
from src.job import Job
from src.logging import logger
from src.regex_utils import generate_regex_patterns_for_blacklisting
import src.utils.browser_utils as browser_utils
import src.utils.time_utils as time_utils


class EnvironmentKeys:
    """Read environment configuration flags."""

    def __init__(self):
        self.skip_apply = self._read_env_key_bool("SKIP_APPLY")
        self.disable_description_filter = self._read_env_key_bool("DISABLE_DESCRIPTION_FILTER")
        logger.debug(f"EnvironmentKeys: skip_apply={self.skip_apply}, disable_description_filter={self.disable_description_filter}")

    @staticmethod
    def _read_env_key(key: str) -> str:
        value = os.getenv(key, "")
        logger.debug(f"Env key {key}: {value}")
        return value

    @staticmethod
    def _read_env_key_bool(key: str) -> bool:
        value = os.getenv(key) == "True"
        logger.debug(f"Env key {key} as bool: {value}")
        return value


class AIHawkJobManager:
    """
    Manages job search and application process on LinkedIn.
    """

    def __init__(self, driver):
        self.driver = driver
        self.set_old_answers = set()
        self.easy_applier_component = None
        self.gpt_answerer = None
        self.resume_generator_manager = None
        self.env_config = EnvironmentKeys()

        # These will be set via set_parameters
        self.company_blacklist = []
        self.title_blacklist = []
        self.location_blacklist = []
        self.positions = []
        self.locations = []
        self.apply_once_at_company = False
        self.base_search_url = ""
        self.seen_jobs = []
        self.min_applicants = JOB_MIN_APPLICATIONS
        self.max_applicants = JOB_MAX_APPLICATIONS
        self.title_blacklist_patterns = []
        self.company_blacklist_patterns = []
        self.location_blacklist_patterns = []
        self.resume_path = None
        self.output_file_directory = Path("job_applications")

    def set_parameters(self, parameters: dict) -> None:
        """Set job search parameters from config."""
        logger.debug("Setting parameters for AIHawkJobManager")

        self.company_blacklist = parameters.get('company_blacklist', []) or []
        self.title_blacklist = parameters.get('title_blacklist', []) or []
        self.location_blacklist = parameters.get('location_blacklist', []) or []
        self.positions = parameters.get('positions', [])
        self.locations = parameters.get('locations', [])
        self.apply_once_at_company = parameters.get('apply_once_at_company', False)
        self.base_search_url = self.get_base_search_url(parameters)
        self.seen_jobs = []

        self.min_applicants = JOB_MIN_APPLICATIONS
        self.max_applicants = JOB_MAX_APPLICATIONS

        # Generate regex patterns for blacklist matching
        self.title_blacklist_patterns = generate_regex_patterns_for_blacklisting(self.title_blacklist)
        self.company_blacklist_patterns = generate_regex_patterns_for_blacklisting(self.company_blacklist)
        self.location_blacklist_patterns = generate_regex_patterns_for_blacklisting(self.location_blacklist)

        # Resume path
        resume_path = parameters.get('uploads', {}).get('resume', None)
        self.resume_path = Path(resume_path) if resume_path and Path(resume_path).exists() else None

        self.output_file_directory = Path(parameters.get('outputFileDirectory', 'job_applications'))
        self.output_file_directory.mkdir(parents=True, exist_ok=True)

        logger.debug("Parameters set successfully")

    def set_gpt_answerer(self, gpt_answerer) -> None:
        """Set the GPT answerer for question handling."""
        self.gpt_answerer = gpt_answerer
        logger.debug("GPT answerer set")

    def set_resume_generator_manager(self, resume_generator_manager) -> None:
        """Set the resume generator manager."""
        self.resume_generator_manager = resume_generator_manager
        logger.debug("Resume generator manager set")

    def start_collecting_data(self) -> None:
        """Start collecting job data without applying."""
        searches = list(product(self.positions, self.locations))
        random.shuffle(searches)

        for position, location in searches:
            location_url = "&location=" + urllib.parse.quote(location)
            job_page_number = -1

            logger.info(f"Collecting data for {position} in {location}")

            try:
                while True:
                    job_page_number += 1
                    logger.info(f"Going to job page {job_page_number}")
                    self.next_job_page(position, location_url, job_page_number)
                    time_utils.medium_sleep()

                    logger.info("Starting the collecting process for this page")
                    self.read_jobs()
                    logger.info("Collecting data on this page has been completed!")

            except Exception as e:
                logger.error(f"Error during data collection: {e}")
                continue

    def start_applying(self) -> None:
        """Start the job application process."""
        logger.debug("Starting job application process")

        # Import here to avoid circular imports
        from src.ai_hawk.linkedIn_easy_applier import AIHawkEasyApplier

        self.easy_applier_component = AIHawkEasyApplier(
            self.driver,
            self.resume_path,
            self.set_old_answers,
            self.gpt_answerer,
            self.resume_generator_manager
        )

        searches = list(product(self.positions, self.locations))
        random.shuffle(searches)

        for position, location in searches:
            location_url = "&location=" + urllib.parse.quote(location)
            job_page_number = -1

            logger.debug(f"Starting the search for {position} in {location}")

            try:
                while True:
                    job_page_number += 1
                    logger.debug(f"Going to job page {job_page_number}")
                    self.next_job_page(position, location_url, job_page_number)
                    time_utils.medium_sleep()

                    logger.debug("Starting the application process for this page...")

                    try:
                        jobs = self.get_jobs_from_page(scroll=True)
                        if not jobs:
                            logger.debug("No more jobs found on this page. Exiting loop.")
                            break
                    except Exception as e:
                        logger.error(f"Failed to retrieve jobs: {e}")
                        break

                    try:
                        self.apply_jobs()
                    except Exception as e:
                        logger.error(f"Error during job application: {e} {traceback.format_exc()}")
                        continue

                    logger.debug("Applying to jobs on this page has been completed!")

                    # Wait between pages
                    time.sleep(MINIMUM_WAIT_TIME_IN_SECONDS)

            except Exception as e:
                logger.error(f"Unexpected error during job search: {e}")
                continue

    def get_jobs_from_page(self, scroll: bool = False) -> List[WebElement]:
        """
        Extract job elements from the current page.

        Args:
            scroll: Whether to scroll the page to load more jobs

        Returns:
            List of job WebElements
        """
        try:
            # Check for "no jobs found" message
            no_jobs_element = self.driver.find_element(By.CLASS_NAME, 'jobs-search-two-pane__no-results-banner--expand')
            if 'No matching jobs found' in no_jobs_element.text or 'unfortunately, things aren' in self.driver.page_source.lower():
                logger.debug("No matching jobs found on this page, skipping.")
                return []

        except NoSuchElementException:
            pass

        try:
            jobs_xpath_query = "//ul[contains(@class, 'scaffold-layout__list-container')]"
            jobs_container = self.driver.find_element(By.XPATH, jobs_xpath_query)

            if scroll:
                jobs_container_scrollable = jobs_container.find_element(By.XPATH, "..")
                logger.warning(f'Scrollable: {browser_utils.is_scrollable(jobs_container_scrollable)}')
                browser_utils.scroll_slow(self.driver, jobs_container_scrollable)
                browser_utils.scroll_slow(self.driver, jobs_container_scrollable, step=300, reverse=True)

            job_element_list = jobs_container.find_elements(
                By.XPATH,
                ".//li[contains(@class, 'jobs-search-results__list-item') and contains(@class, 'ember-view')]"
            )

            if not job_element_list:
                logger.debug("No job class elements found on page, skipping.")
                return []

            return job_element_list

        except NoSuchElementException as e:
            logger.warning(f'No job results found on the page: {traceback.format_exc()}')
            return []

        except Exception as e:
            logger.error(f"Error while fetching job elements: {e} {traceback.format_exc()}")
            return []

    def read_jobs(self) -> None:
        """Read and save job data from current page."""
        job_element_list = self.get_jobs_from_page()
        job_list = [self.job_tile_to_job(job_element) for job_element in job_element_list]

        for job in job_list:
            if self.is_blacklisted(job.title, job.company, job.link, job.location):
                logger.info(f"Blacklisted {job.title} at {job.company} in {job.location}, skipping...")
                self.write_to_file(job, "skipped")
                continue

            try:
                self.write_to_file(job, 'data')
            except Exception as e:
                self.write_to_file(job, "failed")
                continue

    def apply_jobs(self) -> None:
        """Apply to jobs on current page."""
        job_element_list = self.get_jobs_from_page()
        job_list = [self.job_tile_to_job(job_element) for job_element in job_element_list]

        for job in job_list:
            logger.debug(f"Starting application for job: {job.title} at {job.company}")

            if self.is_previously_failed_to_apply(job.link):
                logger.debug(f"Previously failed to apply for {job.title} at {job.company}, skipping...")
                continue

            if self.is_blacklisted(job.title, job.company, job.link, job.location):
                logger.debug(f"Job blacklisted: {job.title} at {job.company} in {job.location}")
                self.write_to_file(job, "skipped", "Job blacklisted")
                continue

            if self.is_already_applied_to_job(job.title, job.company, job.link):
                self.write_to_file(job, "skipped", "Already applied to this job")
                continue

            if self.is_already_applied_to_company(job.company):
                self.write_to_file(job, "skipped", "Already applied to this company")
                continue

            try:
                if job.apply_method not in {"Continue", "Applied", "Apply"}:
                    self.easy_applier_component.job_apply(job)
                    self.write_to_file(job, "success")
                    logger.debug(f"Applied to job: {job.title} at {job.company}")
            except Exception as e:
                logger.error(f"Failed to apply for {job.title} at {job.company}: {e}", exc_info=True)
                self.write_to_file(job, "failed", f"Application error: {str(e)}")
                continue

    def write_to_file(self, job: Job, file_name: str, reason: str = None) -> None:
        """
        Write job application result to JSON file.

        Args:
            job: Job object
            file_name: Base filename (success, failed, skipped, data)
            reason: Optional reason for skipped/failed
        """
        logger.debug(f"Writing job application result to file: {file_name}")

        pdf_path = Path(job.resume_path).resolve() if job.resume_path else Path("")
        pdf_uri = pdf_path.as_uri() if pdf_path.exists() else ""

        data = {
            "company": job.company,
            "job_title": job.title,
            "link": job.link,
            "job_recruiter": job.recruiter_link,
            "job_location": job.location,
            "pdf_path": pdf_uri
        }

        if reason:
            data["reason"] = reason

        file_path = self.output_file_directory / f"{file_name}.json"

        if not file_path.exists():
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([data], f, indent=4, ensure_ascii=False)
                logger.debug(f"Job data written to new file: {file_name}")
        else:
            with open(file_path, 'r+', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    logger.error(f"JSON decode error in file: {file_path}")
                    existing_data = []
                existing_data.append(data)
                f.seek(0)
                json.dump(existing_data, f, indent=4, ensure_ascii=False)
                f.truncate()
                logger.debug(f"Job data appended to existing file: {file_name}")

    def get_base_search_url(self, parameters: dict) -> str:
        """Construct LinkedIn job search URL from parameters."""
        logger.debug("Constructing base search URL")
        url_parts = []

        # Work type filter
        working_type_filter = []
        if parameters.get("onsite"):
            working_type_filter.append("1")
        if parameters.get("remote"):
            working_type_filter.append("2")
        if parameters.get("hybrid"):
            working_type_filter.append("3")

        if working_type_filter:
            url_parts.append(f"f_WT={'%2C'.join(working_type_filter)}")

        # Experience levels
        experience_levels = [
            str(i + 1) for i, (level, v) in enumerate(parameters.get('experience_level', {}).items()) if v
        ]
        if experience_levels:
            url_parts.append(f"f_E={','.join(experience_levels)}")

        # Distance
        url_parts.append(f"distance={parameters.get('distance', 0)}")

        # Job types
        job_types = [
            key[0].upper() for key, value in parameters.get('job_types', {}).items() if value
        ]
        if job_types:
            url_parts.append(f"f_JT={','.join(job_types)}")

        # Date posted
        date_mapping = {
            "all_time": "",
            "month": "&f_TPR=r2592000",
            "week": "&f_TPR=r604800",
            "24_hours": "&f_TPR=r86400"
        }
        date_param = next(
            (v for k, v in date_mapping.items() if parameters.get('date', {}).get(k)),
            ""
        )

        url_parts.append("f_LF=f_AL")
        base_url = "&".join(url_parts)
        full_url = f"?{base_url}{date_param}"

        logger.debug(f"Base search URL constructed: {full_url}")
        return full_url

    def next_job_page(self, position: str, location: str, job_page: int) -> None:
        """Navigate to the next job search page."""
        logger.debug(f"Navigating to next job page: {position} in {location}, page {job_page}")
        encoded_position = urllib.parse.quote(position)
        self.driver.get(
            f"https://www.linkedin.com/jobs/search/{self.base_search_url}&keywords={encoded_position}{location}&start={job_page * 25}"
        )

    def job_tile_to_job(self, job_tile: WebElement) -> Job:
        """Extract job information from a job tile element."""
        logger.debug("Extracting job information from tile")
        job = Job()

        try:
            job.title = job_tile.find_element(By.CLASS_NAME, 'job-card-list__title').find_element(By.TAG_NAME, 'strong').text
            logger.debug(f"Job title extracted: {job.title}")
        except NoSuchElementException:
            logger.warning("Job title is missing.")

        try:
            job.link = job_tile.find_element(By.CLASS_NAME, 'job-card-list__title').get_attribute('href').split('?')[0]
            logger.debug(f"Job link extracted: {job.link}")
        except NoSuchElementException:
            logger.warning("Job link is missing.")

        try:
            job.company = job_tile.find_element(
                By.XPATH,
                ".//div[contains(@class, 'artdeco-entity-lockup__subtitle')]//span"
            ).text
            logger.debug(f"Job company extracted: {job.company}")
        except NoSuchElementException as e:
            logger.warning(f'Job company is missing: {e}')

        try:
            match = re.search(r'/jobs/view/(\d+)/', job.link)
            if match:
                job.id = match.group(1)
                logger.debug(f"Job ID extracted: {job.id}")
            else:
                logger.warning(f"Job ID not found in link: {job.link}")
        except Exception as e:
            logger.warning(f"Failed to extract job ID: {e}", exc_info=True)

        try:
            job.location = job_tile.find_element(By.CLASS_NAME, 'job-card-container__metadata-item').text
        except NoSuchElementException:
            logger.warning("Job location is missing.")

        try:
            job_state = job_tile.find_element(
                By.XPATH,
                ".//ul[contains(@class, 'job-card-list__footer-wrapper')]//li[contains(@class, 'job-card-container__apply-method')]"
            ).text
            job.apply_method = job_state
        except NoSuchElementException:
            try:
                job_state = job_tile.find_element(
                    By.XPATH,
                    ".//ul[contains(@class, 'job-card-list__footer-wrapper')]//li[contains(@class, 'job-card-container__footer-job-state')]"
                ).text
                job.apply_method = "Applied"
                logger.warning(f'Apply method not found, state: {job_state}')
            except NoSuchElementException:
                logger.warning('Apply method and state not found.')

        return job

    def is_blacklisted(self, job_title: str, company: str, link: str, job_location: str) -> bool:
        """Check if job is blacklisted."""
        title_blacklisted = any(
            re.search(pattern, job_title, re.IGNORECASE) for pattern in self.title_blacklist_patterns
        )
        company_blacklisted = any(
            re.search(pattern, company, re.IGNORECASE) for pattern in self.company_blacklist_patterns
        )
        location_blacklisted = any(
            re.search(pattern, job_location, re.IGNORECASE) for pattern in self.location_blacklist_patterns
        )
        link_seen = link in self.seen_jobs

        is_blacklisted = title_blacklisted or company_blacklisted or location_blacklisted or link_seen
        logger.debug(f"Job blacklisted status: {is_blacklisted}")

        return is_blacklisted

    def is_already_applied_to_job(self, job_title: str, company: str, link: str) -> bool:
        """Check if already applied to this specific job."""
        link_seen = link in self.seen_jobs
        if link_seen:
            logger.debug(f"Already applied to job: {job_title} at {company}, skipping...")
        return link_seen

    def is_already_applied_to_company(self, company: str) -> bool:
        """Check if already applied to this company (if apply_once_at_company is True)."""
        if not self.apply_once_at_company:
            return False

        output_files = ["success.json"]
        for file_name in output_files:
            file_path = self.output_file_directory / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        for applied_job in existing_data:
                            if applied_job.get('company', '').strip().lower() == company.strip().lower():
                                logger.debug(f"Already applied at {company} (once per company policy), skipping...")
                                return True
                except json.JSONDecodeError:
                    continue
        return False

    def is_previously_failed_to_apply(self, link: str) -> bool:
        """Check if previously failed to apply to this job link."""
        file_path = self.output_file_directory / "failed.json"

        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            logger.error(f"JSON decode error in file: {file_path}")
            return False

        for data in existing_data:
            if data.get('link') == link:
                return True

        return False