"""
Job Application Profile for ApplyPilot - adapted from Auto_Jobs_Applier_AI_Agent
Parses YAML resume data into structured dataclasses.
"""

import yaml
import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SelfIdentification:
    """Self-identification information for EEO purposes."""
    gender: str = ""
    pronouns: str = ""
    veteran_status: str = ""
    disability_status: str = ""
    ethnicity: str = ""


@dataclass
class LegalAuthorization:
    """Work authorization details for various jurisdictions."""
    # United States
    legally_authorized_us: bool = False
    requires_sponsorship_us: bool = False
    visa_type_us: str = ""

    # European Union
    legally_authorized_eu: bool = False
    requires_sponsorship_eu: bool = False
    visa_type_eu: str = ""

    # Canada
    legally_authorized_canada: bool = False
    requires_sponsorship_canada: bool = False
    visa_type_canada: str = ""

    # United Kingdom
    legally_authorized_uk: bool = False
    requires_sponsorship_uk: bool = False
    visa_type_uk: str = ""

    # Nigeria
    legally_authorized_nigeria: bool = False
    requires_sponsorship_nigeria: bool = False
    visa_type_nigeria: str = ""


@dataclass
class WorkPreferences:
    """Work preference settings."""
    remote_work: bool = True
    in_person_work: bool = False
    open_to_relocation: bool = True
    willing_to_complete_assessments: bool = True
    willing_undergo_drug_test: bool = True
    willing_undergo_background_check: bool = True


@dataclass
class Availability:
    """Availability information."""
    notice_period: str = "Immediately"


@dataclass
class SalaryExpectations:
    """Salary expectation details."""
    currency: str = "USD"
    min_salary: int = 80000
    max_salary: int = 120000


@dataclass
class EducationDetail:
    """Single education entry."""
    degree: str = ""
    field_of_study: str = ""
    institution: str = ""
    graduation_date: str = ""
    gpa: str = ""
    honors: str = ""
    relevant_coursework: str = ""


@dataclass
class ExperienceDetail:
    """Single work experience entry."""
    company: str = ""
    title: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""


@dataclass
class Project:
    """Project portfolio entry."""
    name: str = ""
    description: str = ""
    technologies: List[str] = None
    link: str = ""

    def __post_init__(self):
        if self.technologies is None:
            self.technologies = []


@dataclass
class Certification:
    """Professional certification."""
    name: str = ""
    issuer: str = ""
    date: str = ""
    credential_id: str = ""
    url: str = ""


@dataclass
class Language:
    """Language proficiency."""
    language: str = ""
    proficiency: str = ""


class JobApplicationProfile:
    """
    Main profile class that loads and validates all application data from YAML.
    """

    def __init__(self, yaml_content: str):
        """
        Initialize profile from YAML string.

        Args:
            yaml_content: Raw YAML content from plain_text_resume.yaml
        """
        try:
            data = yaml.safe_load(yaml_content)
            if not data:
                raise ValueError("YAML content is empty or invalid")

            logger.debug("Loading personal information...")
            self.personal_information = data.get("personal_information", {})

            logger.debug("Loading self identification...")
            self.self_identification = SelfIdentification(
                **data.get("self_identification", {})
            )

            logger.debug("Loading legal authorization...")
            self.legal_authorization = LegalAuthorization(
                **data.get("legal_authorization", {})
            )

            logger.debug("Loading work preferences...")
            self.work_preferences = WorkPreferences(
                **data.get("work_preferences", {})
            )

            logger.debug("Loading availability...")
            self.availability = Availability(
                **data.get("availability", {})
            )

            logger.debug("Loading salary expectations...")
            self.salary_expectations = SalaryExpectations(
                **data.get("salary_expectations", {})
            )

            logger.debug("Loading education details...")
            self.education_details = [
                EducationDetail(**edu) for edu in data.get("education_details", [])
            ]

            logger.debug("Loading experience details...")
            self.experience_details = [
                ExperienceDetail(**exp) for exp in data.get("experience_details", [])
            ]

            logger.debug("Loading projects...")
            self.projects = [
                Project(**proj) for proj in data.get("projects", [])
            ]

            logger.debug("Loading certifications...")
            self.certifications = [
                Certification(**cert) for cert in data.get("certifications", [])
            ]

            logger.debug("Loading languages...")
            self.languages = [
                Language(**lang) for lang in data.get("languages", [])
            ]

            logger.debug("Loading interests...")
            self.interests = data.get("interests", [])

            logger.info("JobApplicationProfile loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load JobApplicationProfile: {e}")
            raise

    def __str__(self) -> str:
        """Return formatted string representation of the profile."""
        return f"""
Job Application Profile
=======================
Personal: {self.personal_information.get('full_name', 'N/A')} ({self.personal_information.get('email', 'N/A')})
Location: {self.personal_information.get('city', '')}, {self.personal_information.get('country', '')}
Work Auth: US={self.legal_authorization.legally_authorized_us}, EU={self.legal_authorization.legally_authorized_eu}, CA={self.legal_authorization.legally_authorized_canada}, UK={self.legal_authorization.legally_authorized_uk}, NG={self.legal_authorization.legally_authorized_nigeria}
Experience: {len(self.experience_details)} roles
Education: {len(self.education_details)} entries
Projects: {len(self.projects)} projects
Certifications: {len(self.certifications)} certs
Languages: {len(self.languages)} languages
"""