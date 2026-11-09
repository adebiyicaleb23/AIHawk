"""
Job data model for ApplyPilot - adapted from Auto_Jobs_Applier_AI_Agent
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Job:
    """Data class representing a job posting."""

    id: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    link: str = ""
    apply_method: str = ""
    description: str = ""
    recruiter_link: str = ""

    # These fields are kept for compatibility but should be migrated to JobApplication
    resume_path: str = ""
    cover_letter_path: str = ""

    def set_description(self, description: str) -> None:
        """Set the job description."""
        self.description = description

    def set_recruiter_link(self, recruiter_link: str) -> None:
        """Set the recruiter profile link."""
        self.recruiter_link = recruiter_link

    def formatted_job_information(self) -> str:
        """Return formatted job information as markdown."""
        return f"""
**Position:** {self.title}
**Company:** {self.company}
**Location:** {self.location}
**Recruiter Profile:** {self.recruiter_link if self.recruiter_link else 'Not available'}
**Description:** {self.description if self.description else 'Not available'}
**Apply Method:** {self.apply_method}
**Link:** {self.link}
"""