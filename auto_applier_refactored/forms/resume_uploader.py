"""
Resume Uploader

Handles resume file upload for job applications.
"""

import logging
from pathlib import Path
from playwright.sync_api import Page

from auto_applier_refactored.constants import GENERIC_SELECTORS, RESUME_UPLOAD_DELAY


RESUME_UPLOAD_SELECTORS = [
    "input[data-automation-id='resumeUpload']",
    "input[data-automation-id='attachmentUpload']",
    "input[type='file'][accept*='pdf']",
    "input[type='file']",
]


def upload_resume(page: Page, resume_path: Path) -> bool:
    """
    Upload resume file to the application form.

    Args:
        page: Playwright page object
        resume_path: Path to resume PDF file

    Returns:
        True if upload succeeded, False otherwise
    """
    logger = logging.getLogger(__name__)

    if not resume_path.exists():
        logger.warning(f"Resume file not found: {resume_path}")
        return False

    # Try Workday-specific selectors first
    for sel in RESUME_UPLOAD_SELECTORS:
        finp = page.query_selector(sel)
        if finp and finp.is_visible():
            try:
                finp.set_input_files(str(resume_path))
                _safe_log(f"  Uploaded resume: {resume_path.name}")
                import time
                time.sleep(RESUME_UPLOAD_DELAY)
                return True
            except Exception as e:
                _safe_log(f"  Error uploading resume with {sel}: {e}")
                continue

    # Generic fallback - try all file inputs
    for finp in page.query_selector_all("input[type='file']"):
        try:
            finp.set_input_files(str(resume_path))
            _safe_log(f"  Uploaded resume (fallback): {resume_path.name}")
            import time
            time.sleep(RESUME_UPLOAD_DELAY)
            return True
        except Exception:
            continue

    logger.warning(f"Could not find file upload input for resume: {resume_path.name}")
    return False


def _safe_log(msg: str) -> None:
    """Log message with safe ASCII encoding."""
    safe_msg = msg.encode('ascii', 'replace').decode('ascii')
    logging.getLogger(__name__).info(safe_msg)