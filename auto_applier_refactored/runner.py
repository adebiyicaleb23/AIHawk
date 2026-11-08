"""
ApplyPilot Auto-Applier Runner

Main orchestration module for auto-applying to jobs.
"""

import logging
import time
import sqlite3
from pathlib import Path
from typing import List, Dict

from playwright.sync_api import sync_playwright

from auto_applier_refactored.models import Job, Candidate, ApplicationResult, ApplicationStatus, AutoApplySummary
from auto_applier_refactored.config import load_candidate_profile, load_gemini_keys, get_tailored_resume_path
from auto_applier_refactored.auth import get_auth_handler
from auto_applier_refactored.forms import FormFiller, upload_resume
from auto_applier_refactored.navigation import PageNavigator, normalize_url
from auto_applier_refactored.gemini_client import GeminiClient
from auto_applier_refactored.constants import (
    get_db_path,
    BROWSER_ARGS,
    USER_AGENT,
    PAGE_LOAD_TIMEOUT,
)
from auto_applier_refactored.exceptions import (
    ApplyPilotError,
    ConfigurationError,
    AuthenticationError,
    NavigationError,
    FormFillError,
    ResumeNotFoundError,
)

logger = logging.getLogger(__name__)


def run_auto_apply(headless: bool = True) -> Dict[str, int]:
    """
    Main entry point for auto-apply.

    Args:
        headless: Run browser in headless mode

    Returns:
        Dict with applied, ready, total counts
    """
    # Load configuration
    candidate = load_candidate_profile()
    gemini_keys = load_gemini_keys()
    gemini = GeminiClient(gemini_keys)

    # Fetch eligible jobs
    jobs = fetch_eligible_jobs()
    if not jobs:
        logger.info("No unapplied tailored jobs pending.")
        return {"applied": 0, "ready": 0, "total": 0}

    logger.info(f"=== Starting Auto-Apply pass for {len(jobs)} tailored jobs ===")

    applied_count = 0
    ready_count = 0
    error_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=BROWSER_ARGS
        )
        context = browser.new_context(user_agent=USER_AGENT)

        for job in jobs:
            try:
                result = process_job(context, job, candidate, gemini)
                update_job_status(job, result)

                if result.is_success():
                    applied_count += 1
                    print(f"[SUCCESS] Applied to '{job.title}' at {job.site or 'company site'}!", flush=True)
                elif result.is_ready():
                    ready_count += 1
                    print(f"[READY] Tailored & prepared: '{job.title}' | {job.application_url or job.url}", flush=True)
                else:
                    error_count += 1
                    print(f"[ERROR] Failed to apply to '{job.title}': {result.error_message}", flush=True)

            except Exception as e:
                error_count += 1
                error_msg = str(e).encode('ascii', 'replace').decode('ascii')
                logger.warning(f"Error on '{job.title}': {error_msg}")
                update_job_status(job, ApplicationResult(
                    job_url=job.url,
                    status=ApplicationStatus.ERROR,
                    error_message=error_msg
                ))

        browser.close()

    gemini.close()

    summary = AutoApplySummary(
        applied=applied_count,
        ready=ready_count,
        total=len(jobs),
        errors=error_count
    )
    logger.info(f"Auto-apply pass complete: {summary.applied} submitted, {summary.ready} prepared, {summary.errors} errors.")
    return {"applied": applied_count, "ready": ready_count, "total": len(jobs)}


def fetch_eligible_jobs() -> List[Job]:
    """Fetch jobs eligible for auto-apply from database."""
    db_path = get_db_path()

    if not db_path.exists():
        logger.warning(f"Database not found at {db_path}")
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT url, title, site, application_url, tailored_resume_path, fit_score,
               apply_status, full_description, salary, location, description,
               strategy, discovered_at, detail_scraped_at, detail_error,
               score_reasoning, scored_at, tailored_at, tailor_attempts,
               cover_letter_path, cover_letter_at, cover_attempts,
               applied_at, apply_error, apply_attempts, agent_id,
               last_attempted_at, apply_duration_ms, apply_task_id,
               verification_confidence
        FROM jobs
        WHERE tailored_resume_path IS NOT NULL
          AND (apply_status IS NULL OR apply_status NOT IN ('applied', 'portal_gated'))
        ORDER BY fit_score DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    jobs = []
    for row in rows:
        job = Job(
            url=row["url"],
            title=row["title"],
            site=row["site"],
            application_url=row["application_url"],
            tailored_resume_path=Path(row["tailored_resume_path"]),
            fit_score=row["fit_score"],
            apply_status=row["apply_status"],
            full_description=row["full_description"],
            salary=row["salary"],
            location=row["location"],
            description=row["description"],
            strategy=row["strategy"],
            discovered_at=row["discovered_at"],
            detail_scraped_at=row["detail_scraped_at"],
            detail_error=row["detail_error"],
            score_reasoning=row["score_reasoning"],
            scored_at=row["scored_at"],
            tailored_at=row["tailored_at"],
            tailor_attempts=row["tailor_attempts"] or 0,
            cover_letter_path=row["cover_letter_path"],
            cover_letter_at=row["cover_letter_at"],
            cover_attempts=row["cover_attempts"] or 0,
            applied_at=row["applied_at"],
            apply_error=row["apply_error"],
            apply_attempts=row["apply_attempts"] or 0,
            agent_id=row["agent_id"],
            last_attempted_at=row["last_attempted_at"],
            apply_duration_ms=row["apply_duration_ms"],
            apply_task_id=row["apply_task_id"],
            verification_confidence=row["verification_confidence"],
        )
        jobs.append(job)

    return jobs


def process_job(context, job: Job, candidate: Candidate, gemini: GeminiClient) -> ApplicationResult:
    """
    Process a single job application.

    Args:
        context: Playwright browser context
        job: Job to apply to
        candidate: Candidate profile
        gemini: Gemini client for screening questions

    Returns:
        ApplicationResult
    """
    start_time = time.time()
    page = context.new_page()

    try:
        # Step 1: Navigate to job/apply URL
        target_url = normalize_url(job.application_url or job.url, job.url, job.site)
        logger.info(f"\n---> [{job.fit_score}/10] '{job.title}' at {job.site or 'Web'}")
        logger.info(f"     URL: {target_url}")

        # Resume file
        resume_file = get_tailored_resume_path(job)
        logger.info(f"     Resume attachment: {resume_file.name}")

        page.goto(target_url, timeout=PAGE_LOAD_TIMEOUT, wait_until="domcontentloaded")
        time.sleep(3)

        # Step 2: Navigate to application form
        navigator = PageNavigator(page)
        navigator.click_apply_button()
        navigator.handle_post_apply_navigation()

        # Step 3: Handle authentication
        portal = _detect_portal(page.url)
        auth_handler = get_auth_handler(page, page.url)
        auth_handler.authenticate(page, candidate)
        time.sleep(2)

        # Step 4: Multi-step form progression
        return _process_form_steps(page, navigator, job, candidate, gemini, resume_file, start_time)

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return ApplicationResult(
            job_url=job.url,
            status=ApplicationStatus.ERROR,
            error_message=str(e),
            duration_ms=duration_ms
        )
    finally:
        page.close()


def _detect_portal(url: str) -> str:
    """Detect portal type from URL."""
    from auto_applier_refactored.navigation.url_resolver import (
        is_workday_url, is_greenhouse_url, is_lever_url, is_linkedin_url
    )
    if is_workday_url(url):
        return "workday"
    elif is_greenhouse_url(url):
        return "greenhouse"
    elif is_lever_url(url):
        return "lever"
    elif is_linkedin_url(url):
        return "linkedin"
    return "generic"


def _process_form_steps(
    page: Page,
    navigator: PageNavigator,
    job: Job,
    candidate: Candidate,
    gemini: GeminiClient,
    resume_file: Path,
    start_time: float
) -> ApplicationResult:
    """Process multi-step application form."""

    filler = FormFiller(candidate, gemini, portal=_detect_portal(page.url))
    max_steps = navigator.get_max_steps()
    submitted = False

    for step_num in range(max_steps):
        logger.info(f"  Form step {step_num + 1}/{max_steps}")

        # Wait for form to load
        time.sleep(2)

        # Handle cookie consent
        navigator.handle_cookie_consent()
        time.sleep(1)

        # Fill form
        filler.fill(page)
        time.sleep(1)

        # Upload resume
        upload_resume(page, resume_file)

        # Try Submit
        if navigator.click_submit():
            submitted = True
            duration_ms = int((time.time() - start_time) * 1000)
            logger.info("  Submit clicked!")
            return ApplicationResult(
                job_url=job.url,
                status=ApplicationStatus.APPLIED,
                applied_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                duration_ms=duration_ms
            )

        # Try Next/Continue
        if not navigator.click_next():
            logger.info("  No more navigation buttons found")
            break

        time.sleep(3)  # Wait for step transition

    # Not submitted - ready for manual review
    duration_ms = int((time.time() - start_time) * 1000)
    return ApplicationResult(
        job_url=job.url,
        status=ApplicationStatus.READY_TO_APPLY,
        duration_ms=duration_ms
    )


def update_job_status(job: Job, result: ApplicationResult) -> None:
    """Update job status in database."""
    db_path = get_db_path()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    status = result.status.value
    applied_at = result.applied_at
    error_msg = result.error_message

    cursor.execute(
        "UPDATE jobs SET apply_status=?, applied_at=?, apply_error=?, "
        "apply_attempts=apply_attempts+1, last_attempted_at=?, apply_duration_ms=? WHERE url=?",
        (
            status,
            applied_at,
            error_msg,
            time.strftime("%Y-%m-%d %H:%M:%S"),
            result.duration_ms,
            job.url
        )
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    run_auto_apply()