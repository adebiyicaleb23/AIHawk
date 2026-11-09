"""
Job Application Saver for ApplyPilot - adapted from Auto_Jobs_Applier_AI_Agent
Persists job application data to disk.
"""

import json
import shutil
from pathlib import Path
from typing import Optional

from config import JOB_APPLICATIONS_DIR
from src.job import Job
from src.job_application import JobApplication
from src.logging import logger


class ApplicationSaver:
    """Handles saving job application data to the filesystem."""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the saver.

        Args:
            output_dir: Custom output directory. Defaults to JOB_APPLICATIONS_DIR from config.
        """
        self.output_dir = output_dir or Path(JOB_APPLICATIONS_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_application_directory(self, job: Job) -> Path:
        """
        Create a directory for the job application.

        Args:
            job: The job object

        Returns:
            Path to the created directory
        """
        # Sanitize directory name
        safe_company = "".join(c for c in job.company if c.isalnum() or c in (" ", "-", "_")).strip()
        safe_title = "".join(c for c in job.title if c.isalnum() or c in (" ", "-", "_")).strip()
        dir_name = f"{job.id} - {safe_company} {safe_title}" if job.id else f"{safe_company} {safe_title}"

        app_dir = self.output_dir / dir_name
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir

    def save_application_details(self, app_dir: Path, job_application: JobApplication) -> None:
        """Save application questions and answers to JSON."""
        file_path = app_dir / "job_application.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(job_application.application, f, indent=4, ensure_ascii=False)
        logger.debug(f"Saved application details to {file_path}")

    def save_job_description(self, app_dir: Path, job: Job) -> None:
        """Save job description to JSON."""
        file_path = app_dir / "job_description.json"
        job_data = {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "link": job.link,
            "apply_method": job.apply_method,
            "description": job.description,
            "recruiter_link": job.recruiter_link,
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(job_data, f, indent=4, ensure_ascii=False)
        logger.debug(f"Saved job description to {file_path}")

    def save_file(self, app_dir: Path, source_path: str, target_name: str) -> bool:
        """
        Copy a file to the application directory.

        Args:
            app_dir: Target application directory
            source_path: Source file path
            target_name: Target filename

        Returns:
            True if successful, False otherwise
        """
        try:
            src = Path(source_path)
            if not src.exists():
                logger.warning(f"Source file not found: {source_path}")
                return False

            dst = app_dir / target_name
            shutil.copy2(src, dst)
            logger.debug(f"Copied {source_path} to {dst}")
            return True
        except Exception as e:
            logger.error(f"Failed to copy file {source_path}: {e}")
            return False

    def save(self, job_application: JobApplication) -> Optional[Path]:
        """
        Save complete job application data.

        Args:
            job_application: The JobApplication object to save

        Returns:
            Path to the application directory, or None if failed
        """
        job = job_application.job

        # Create application directory
        app_dir = self.create_application_directory(job)

        # Save JSON files
        self.save_application_details(app_dir, job_application)
        self.save_job_description(app_dir, job)

        # Copy resume and cover letter if paths are set
        if job_application.resume_path:
            self.save_file(app_dir, job_application.resume_path, "resume.pdf")

        if job_application.cover_letter_path:
            self.save_file(app_dir, job_application.cover_letter_path, "cover_letter.pdf")

        logger.info(f"Saved application for {job.title} at {job.company} to {app_dir}")
        return app_dir


# Static method for backward compatibility
def save_application(job_application: JobApplication, output_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Convenience function to save a job application.

    Args:
        job_application: The JobApplication to save
        output_dir: Optional custom output directory

    Returns:
        Path to the application directory, or None if failed
    """
    saver = ApplicationSaver(output_dir)
    return saver.save(job_application)