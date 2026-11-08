"""
Field Mapper

Builds field mappings from candidate data for form filling.
"""

from dataclasses import dataclass
from typing import List

from auto_applier_refactored.models import Candidate
from auto_applier_refactored.constants import (
    WORKDAY_FIELD_MAPPINGS,
    GENERIC_SELECTORS,
    WORKDAY_SELECTORS,
)


@dataclass
class FieldMapping:
    """Mapping of selectors to a candidate value."""
    selectors: List[str]
    value: str
    label: str


def build_field_mappings(candidate: Candidate, portal: str = "generic") -> List[FieldMapping]:
    """
    Build all field mappings from candidate data.

    Args:
        candidate: Candidate profile
        portal: Portal type ("workday", "greenhouse", "lever", "generic")

    Returns:
        List of FieldMapping objects in fill order
    """
    mappings = []

    # Workday-specific fields (data-automation-id)
    if portal == "workday":
        for field_id, candidate_attr in WORKDAY_FIELD_MAPPINGS.items():
            value = getattr(candidate, candidate_attr, "")
            if value:
                selectors = [f"[data-automation-id='{field_id}'], input[id='{field_id}']"]
                mappings.append(FieldMapping(selectors, value, f"Workday {field_id}"))

    # Common fields for all portals
    common_mappings = [
        # Email
        (GENERIC_SELECTORS["email_field"], candidate.email, "email"),
        # Name fields
        (GENERIC_SELECTORS["first_name_field"], candidate.first_name, "first name"),
        (GENERIC_SELECTORS["last_name_field"], candidate.last_name, "last name"),
        # Phone
        (GENERIC_SELECTORS["phone_field"], candidate.phone, "phone"),
        # Location
        (["input[name*='city' i], input[id*='city' i], input[placeholder*='city' i]"], candidate.city, "city"),
        (["input[name*='country' i], input[id*='country' i]"], candidate.country, "country"),
        # URLs
        (["input[type='url'], input[name*='linkedin' i], input[id*='linkedin' i]"], candidate.linkedin_url, "LinkedIn URL"),
        (["input[name*='portfolio' i], input[name*='website' i], input[name*='github' i]"], candidate.portfolio_url, "Portfolio URL"),
        # DOB
        (GENERIC_SELECTORS["dob_field"], candidate.dob, "DOB"),
        (GENERIC_SELECTORS["dob_day_field"], candidate.dob_day, "DOB day"),
        (GENERIC_SELECTORS["dob_month_field"], candidate.dob_month, "DOB month"),
        (GENERIC_SELECTORS["dob_year_field"], candidate.dob_year, "DOB year"),
    ]

    for selectors, value, label in common_mappings:
        if value:
            mappings.append(FieldMapping(selectors, value, label))

    return mappings


def build_screening_question_mapping(question_text: str) -> FieldMapping:
    """Create a field mapping for a screening question (answered by Gemini)."""
    return FieldMapping(
        selectors=["textarea", "input[type='text']:not([readonly])"],
        value="",  # Will be filled by Gemini
        label=question_text
    )