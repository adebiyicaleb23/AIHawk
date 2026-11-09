"""
Job Context data model for ApplyPilot - adapted from Auto_Jobs_Applier_AI_Agent
"""

from dataclasses import dataclass
from src.job import Job
from src.job_application import JobApplication


@dataclass
class JobContext:
    """Container for job and job application context."""

    job: Job = None
    job_application: JobApplication = None