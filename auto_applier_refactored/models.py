"""
ApplyPilot Data Models

Immutable dataclasses for type-safe data transfer between modules.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import Optional


class ApplicationStatus(Enum):
    """Application status enumeration."""
    APPLIED = "applied"
    READY_TO_APPLY = "ready_to_apply"
    PORTAL_GATED = "portal_gated"
    ERROR = "error"


@dataclass(frozen=True)
class Candidate:
    """Immutable candidate profile data."""
    email: str
    password: str
    full_name: str
    first_name: str
    last_name: str
    phone: str
    city: str
    country: str
    linkedin_url: str
    portfolio_url: str
    dob: str
    dob_day: str
    dob_month: str
    dob_year: str
    postal_code: str = ""
    province_state: str = ""
    github_url: str = ""
    website_url: str = ""
    address: str = ""

    @property
    def name_parts(self) -> tuple[str, str]:
        """Return (first_name, last_name) tuple."""
        return (self.first_name, self.last_name)


@dataclass(frozen=True)
class Job:
    """Immutable job data from database."""
    url: str
    title: str
    site: Optional[str]
    application_url: Optional[str]
    tailored_resume_path: Path
    fit_score: int
    apply_status: Optional[str]
    full_description: Optional[str] = None
    salary: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    strategy: Optional[str] = None
    discovered_at: Optional[str] = None
    detail_scraped_at: Optional[str] = None
    detail_error: Optional[str] = None
    score_reasoning: Optional[str] = None
    scored_at: Optional[str] = None
    tailored_at: Optional[str] = None
    tailor_attempts: int = 0
    cover_letter_path: Optional[str] = None
    cover_letter_at: Optional[str] = None
    cover_attempts: int = 0
    applied_at: Optional[str] = None
    apply_error: Optional[str] = None
    apply_attempts: int = 0
    agent_id: Optional[str] = None
    last_attempted_at: Optional[str] = None
    apply_duration_ms: Optional[int] = None
    apply_task_id: Optional[str] = None
    verification_confidence: Optional[str] = None

    @property
    def is_tailored(self) -> bool:
        """Check if job has a tailored resume."""
        return self.tailored_resume_path is not None and self.tailored_resume_path != Path("")

    @property
    def is_applied(self) -> bool:
        """Check if job has been applied to."""
        return self.apply_status == ApplicationStatus.APPLIED.value


@dataclass(frozen=True)
class ApplicationResult:
    """Result of an application attempt."""
    job_url: str
    status: ApplicationStatus
    error_message: Optional[str] = None
    applied_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    def is_success(self) -> bool:
        """Check if application was successful."""
        return self.status == ApplicationStatus.APPLIED

    def is_ready(self) -> bool:
        """Check if application is ready for manual review."""
        return self.status == ApplicationStatus.READY_TO_APPLY


@dataclass(frozen=True)
class AutoApplySummary:
    """Summary of auto-apply run."""
    applied: int
    ready: int
    total: int
    errors: int

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total == 0:
            return 0.0
        return self.applied / self.total