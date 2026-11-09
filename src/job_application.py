"""
Job Application data model for ApplyPilot - adapted from Auto_Jobs_Applier_AI_Agent
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
from src.job import Job


@dataclass
class JobApplication:
    """Data class representing a job application."""

    job: Job
    application: List[Dict[str, Any]] = field(default_factory=list)
    resume_path: str = ""
    cover_letter_path: str = ""

    def save_application_data(self, application_questions: Dict[str, Any]) -> None:
        """Save application questions and answers."""
        self.application.append(application_questions)

    def set_resume_path(self, resume_path: str) -> None:
        """Set the path to the resume file."""
        self.resume_path = resume_path

    def set_cover_letter_path(self, cover_letter_path: str) -> None:
        """Set the path to the cover letter file."""
        self.cover_letter_path = cover_letter_path