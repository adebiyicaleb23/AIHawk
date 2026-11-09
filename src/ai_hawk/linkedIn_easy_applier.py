"""
LinkedIn Easy Applier for ApplyPilot - adapted from Auto_Jobs_Applier_AI_Agent
Handles the actual job application form filling and submission.
"""

import json
import os
import time
import traceback
from pathlib import Path
from typing import Optional, List, Dict, Any

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)

from src.job import Job
from src.logging import logger
import src.utils.time_utils as time_utils
import src.utils.browser_utils as browser_utils


class AIHawkEasyApplier:
    """
    Handles LinkedIn Easy Apply application process.
    """

    def __init__(
        self,
        driver,
        resume_path: Optional[Path],
        old_answers: set,
        gpt_answerer,
        resume_generator_manager
    ):
        self.driver = driver
        self.resume_path = resume_path
        self.set_old_answers = old_answers
        self.gpt_answerer = gpt_answerer
        self.resume_generator_manager = resume_generator_manager
        self.wait = WebDriverWait(driver, 10)

        # Answer cache file
        self.answers_file = Path("answers.json")
        self.answers_cache = self._load_answers_cache()

    def _load_answers_cache(self) -> Dict[str, str]:
        """Load cached answers from file."""
        if self.answers_file.exists():
            try:
                with open(self.answers_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load answers cache: {e}")
        return {}

    def _save_answers_cache(self) -> None:
        """Save answers cache to file."""
        try:
            with open(self.answers_file, 'w', encoding='utf-8') as f:
                json.dump(self.answers_cache, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save answers cache: {e}")

    def job_apply(self, job: Job) -> bool:
        """
        Main entry point for applying to a job.

        Args:
            job: Job object to apply to

        Returns:
            True if application submitted successfully
        """
        logger.info(f"Starting application for: {job.title} at {job.company}")

        try:
            # Navigate to job page
            self.driver.get(job.link)
            time_utils.medium_sleep()

            # Click Easy Apply button
            if not self._click_easy_apply_button():
                logger.warning("Easy Apply button not found or not clickable")
                return False

            # Fill application form
            return self._fill_application_form(job)

        except Exception as e:
            logger.error(f"Error during job application: {e} {traceback.format_exc()}")
            return False

    def _click_easy_apply_button(self) -> bool:
        """Find and click the Easy Apply button."""
        try:
            # Wait for page load
            time_utils.medium_sleep()

            # Try multiple selectors for Easy Apply button
            selectors = [
                "//button[contains(@class, 'jobs-apply-button')]",
                "//button[contains(., 'Easy Apply')]",
                "//button[contains(@aria-label, 'Easy Apply')]",
                "//div[contains(@class, 'jobs-apply-button')]//button",
            ]

            for selector in selectors:
                try:
                    button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    button.click()
                    logger.debug("Clicked Easy Apply button")
                    time_utils.medium_sleep()
                    return True
                except TimeoutException:
                    continue

            logger.warning("Easy Apply button not found")
            return False

        except Exception as e:
            logger.error(f"Error clicking Easy Apply button: {e}")
            return False

    def _fill_application_form(self, job: Job) -> bool:
        """Fill out the multi-step application form."""
        try:
            max_steps = 10  # Safety limit
            step = 0

            while step < max_steps:
                step += 1
                logger.debug(f"Processing application step {step}")

                # Check if we're on a review/submit step
                if self._is_review_step():
                    return self._submit_application()

                # Check for error messages
                if self._check_form_errors():
                    logger.error("Form errors detected")
                    return False

                # Fill current step
                self._process_current_step(job)

                # Click next/continue button
                if not self._click_next_button():
                    logger.debug("No next button found, might be final step")
                    break

                time_utils.medium_sleep()

            # Try to submit if we're at the end
            return self._submit_application()

        except Exception as e:
            logger.error(f"Error filling application form: {e} {traceback.format_exc()}")
            return False

    def _is_review_step(self) -> bool:
        """Check if current step is review/submit step."""
        try:
            # Look for review/submit indicators
            review_indicators = [
                "//button[contains(., 'Review')]",
                "//button[contains(., 'Submit')]",
                "//span[contains(., 'Review your application')]",
                "//h3[contains(., 'Review')]",
            ]

            for indicator in review_indicators:
                elements = self.driver.find_elements(By.XPATH, indicator)
                if elements and any(e.is_displayed() for e in elements):
                    return True
        except Exception:
            pass
        return False

    def _check_form_errors(self) -> bool:
        """Check for form validation errors."""
        try:
            error_elements = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'artdeco-inline-feedback--error')] | "
                "//p[contains(@class, 'error')] | "
                "//span[contains(@class, 'error')]"
            )
            return any(e.is_displayed() and e.text.strip() for e in error_elements)
        except Exception:
            return False

    def _process_current_step(self, job: Job) -> None:
        """Process all form fields in the current step."""
        try:
            # Find all form fields in the current modal
            form_fields = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'jobs-easy-apply-form-section')]//*[self::input or self::textarea or self::select]"
            )

            for field in form_fields:
                try:
                    if not field.is_displayed():
                        continue

                    field_type = field.get_attribute("type")
                    tag_name = field.tag_name.lower()

                    if tag_name == "input" and field_type == "file":
                        self._handle_file_upload(field, job)
                    elif tag_name == "select":
                        self._handle_dropdown(field)
                    elif tag_name == "input" and field_type in ("radio", "checkbox"):
                        self._handle_radio_checkbox(field)
                    elif tag_name in ("input", "textarea"):
                        self._handle_text_field(field, job)

                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    logger.debug(f"Error processing field: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error processing current step: {e}")

    def _handle_file_upload(self, field, job: Job) -> None:
        """Handle resume/cover letter file upload."""
        try:
            # Determine if this is resume or cover letter upload
            label_text = ""
            try:
                label = field.find_element(By.XPATH, "./preceding::label[1]")
                label_text = label.text.lower()
            except NoSuchElementException:
                pass

            if "resume" in label_text or "cv" in label_text:
                file_path = str(self.resume_path) if self.resume_path else ""
            elif "cover" in label_text or "letter" in label_text:
                # Generate cover letter if needed
                file_path = ""  # TODO: Generate cover letter
            else:
                file_path = str(self.resume_path) if self.resume_path else ""

            if file_path and Path(file_path).exists():
                field.send_keys(file_path)
                logger.debug(f"Uploaded file: {file_path}")
            else:
                logger.warning(f"No file available for upload (label: {label_text})")

        except Exception as e:
            logger.error(f"Error handling file upload: {e}")

    def _handle_dropdown(self, field) -> None:
        """Handle dropdown/select fields."""
        try:
            select = Select(field)
            options = [opt.text for opt in select.options if opt.text.strip()]

            if not options:
                return

            # Try to select a reasonable default (first non-empty option)
            for i, option in enumerate(options):
                if option and option.lower() not in ("select", "choose", "--"):
                    select.select_by_index(i)
                    logger.debug(f"Selected dropdown option: {option}")
                    break

        except Exception as e:
            logger.debug(f"Error handling dropdown: {e}")

    def _handle_radio_checkbox(self, field) -> None:
        """Handle radio buttons and checkboxes."""
        try:
            # For radio buttons, select the first option
            # For checkboxes (like terms of service), check them
            field_type = field.get_attribute("type")

            if field_type == "radio":
                if not field.is_selected():
                    field.click()
                    logger.debug("Selected radio button")
            elif field_type == "checkbox":
                if not field.is_selected():
                    field.click()
                    logger.debug("Checked checkbox")

        except Exception as e:
            logger.debug(f"Error handling radio/checkbox: {e}")

    def _handle_text_field(self, field, job: Job) -> None:
        """Handle text input and textarea fields."""
        try:
            # Get field identifier
            field_id = field.get_attribute("id") or ""
            field_name = field.get_attribute("name") or ""
            field_aria = field.get_attribute("aria-label") or ""
            field_placeholder = field.get_attribute("placeholder") or ""

            # Combine identifiers to understand the question
            identifiers = " ".join([field_id, field_name, field_aria, field_placeholder]).lower()

            # Skip if already filled
            current_value = field.get_attribute("value") or ""
            if current_value.strip():
                logger.debug(f"Field already filled: {identifiers[:50]}")
                return

            # Check cache first
            cache_key = identifiers[:200]
            if cache_key in self.answers_cache:
                answer = self.answers_cache[cache_key]
                field.send_keys(answer)
                logger.debug(f"Used cached answer for: {identifiers[:50]}")
                return

            # Check old answers set
            if cache_key in self.set_old_answers:
                logger.debug(f"Skipping previously answered: {identifiers[:50]}")
                return

            # Use GPT answerer if available
            if self.gpt_answerer:
                try:
                    question_text = self._extract_question_text(field)
                    if question_text:
                        answer = self.gpt_answerer.answer_question(
                            question=question_text,
                            job_description=job.description,
                            resume=job.resume_path
                        )
                        if answer:
                            field.send_keys(answer)
                            self.answers_cache[cache_key] = answer
                            self._save_answers_cache()
                            logger.debug(f"GPT answered: {question_text[:50]} -> {answer[:50]}")
                            return
                except Exception as e:
                    logger.debug(f"GPT answerer failed: {e}")

            # Default handling for common fields
            answer = self._get_default_answer(identifiers, job)
            if answer:
                field.send_keys(answer)
                self.answers_cache[cache_key] = answer
                self._save_answers_cache()

        except Exception as e:
            logger.debug(f"Error handling text field: {e}")

    def _extract_question_text(self, field) -> str:
        """Extract the question text associated with a field."""
        try:
            # Try to find associated label
            label_selectors = [
                "./preceding::label[1]",
                "./ancestor::div[contains(@class, 'form-field')]//label",
                "./preceding::span[contains(@class, 'label')][1]",
            ]

            for selector in label_selectors:
                try:
                    label = field.find_element(By.XPATH, selector)
                    text = label.text.strip()
                    if text:
                        return text
                except NoSuchElementException:
                    continue

            # Fallback to aria-label or placeholder
            return field.get_attribute("aria-label") or field.get_attribute("placeholder") or ""

        except Exception:
            return ""

    def _get_default_answer(self, identifiers: str, job: Job) -> str:
        """Get default answer for common field types."""
        identifiers = identifiers.lower()

        # Phone number
        if any(keyword in identifiers for keyword in ["phone", "mobile", "telephone"]):
            return "+2347050301256"

        # Email
        if "email" in identifiers:
            return "adebiyicaleb222@gmail.com"

        # Years of experience
        if "year" in identifiers and "experience" in identifiers:
            return "5"

        # Salary expectations
        if "salary" in identifiers or "compensation" in identifiers or "pay" in identifiers:
            return "80000-120000"

        # Notice period
        if "notice" in identifiers or "available" in identifiers:
            return "Immediately"

        # LinkedIn profile
        if "linkedin" in identifiers:
            return "https://www.linkedin.com/in/iyanuoluwa-adebiyi-5a3a78431"

        # Portfolio/GitHub
        if "portfolio" in identifiers or "github" in identifiers or "website" in identifiers:
            return "https://iyanu-portfolio-pi.vercel.app/"

        # Location
        if "location" in identifiers or "city" in identifiers or "address" in identifiers:
            return "Abuja, FCT, Nigeria"

        # Work authorization
        if "authorization" in identifiers or "visa" in identifiers or "sponsor" in identifiers:
            return "Require H-1B sponsorship for US; authorized in Nigeria"

        return ""

    def _click_next_button(self) -> bool:
        """Click the Next/Continue button."""
        try:
            next_selectors = [
                "//button[contains(., 'Next')]",
                "//button[contains(., 'Continue')]",
                "//button[contains(@aria-label, 'Continue')]",
                "//button[contains(@class, 'artdeco-button--primary')]",
            ]

            for selector in next_selectors:
                try:
                    button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    # Make sure it's not a submit button
                    button_text = button.text.lower()
                    if "submit" in button_text or "review" in button_text:
                        continue

                    button.click()
                    logger.debug(f"Clicked next button: {button_text}")
                    return True
                except TimeoutException:
                    continue

            return False

        except Exception as e:
            logger.debug(f"Error clicking next button: {e}")
            return False

    def _submit_application(self) -> bool:
        """Submit the application on the review step."""
        try:
            submit_selectors = [
                "//button[contains(., 'Submit application')]",
                "//button[contains(., 'Submit')]",
                "//button[contains(@aria-label, 'Submit')]",
            ]

            for selector in submit_selectors:
                try:
                    button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    button.click()
                    logger.info("Application submitted successfully!")
                    time_utils.medium_sleep()
                    return True
                except TimeoutException:
                    continue

            logger.warning("Submit button not found")
            return False

        except Exception as e:
            logger.error(f"Error submitting application: {e}")
            return False

    def _discard_application(self) -> None:
        """Discard the current application."""
        try:
            discard_selectors = [
                "//button[contains(., 'Discard')]",
                "//button[contains(@aria-label, 'Discard')]",
            ]

            for selector in discard_selectors:
                try:
                    button = self.driver.find_element(By.XPATH, selector)
                    if button.is_displayed():
                        button.click()
                        # Confirm discard
                        confirm_selectors = [
                            "//button[contains(., 'Discard')]",
                            "//button[contains(., 'Yes')]",
                        ]
                        for confirm_selector in confirm_selectors:
                            try:
                                confirm_btn = self.wait.until(
                                    EC.element_to_be_clickable((By.XPATH, confirm_selector))
                                )
                                confirm_btn.click()
                                break
                            except TimeoutException:
                                continue
                        logger.info("Application discarded")
                        return
                except NoSuchElementException:
                    continue
        except Exception as e:
            logger.debug(f"Error discarding application: {e}")