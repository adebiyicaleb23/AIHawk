"""
ApplyPilot Auto-Applier Package

Automatically creates accounts and applies to jobs on ANY portal:
- Workday (myworkdayjobs.com)
- Greenhouse (boards.greenhouse.io)
- Lever (jobs.lever.co)
- LinkedIn Easy Apply
- Generic portals with signup forms
"""

from auto_applier_refactored.runner import run_auto_apply
from auto_applier_refactored.models import Job, Candidate, ApplicationResult, ApplicationStatus
from auto_applier_refactored.config import load_candidate_profile
from auto_applier_refactored.exceptions import (
    ApplyPilotError,
    ConfigurationError,
    AuthenticationError,
    NavigationError,
    FormFillError,
    GeminiError,
)

__all__ = [
    "run_auto_apply",
    "Job",
    "Candidate",
    "ApplicationResult",
    "ApplicationStatus",
    "load_candidate_profile",
    "ApplyPilotError",
    "ConfigurationError",
    "AuthenticationError",
    "NavigationError",
    "FormFillError",
    "GeminiError",
]

__version__ = "2.0.0"