"""
ApplyPilot Configuration Loader

Loads candidate profile from environment variables and profile.json.
NO HARDCODED DEFAULTS - raises ConfigurationError if required fields missing.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional

from auto_applier_refactored.models import Candidate
from auto_applier_refactored.exceptions import ConfigurationError, ProfileLoadError
from auto_applier_refactored.constants import get_profile_path, get_applypilot_dir

log = logging.getLogger(__name__)

# Required fields that MUST be present (no defaults)
REQUIRED_FIELDS = [
    "email",
    "password",
    "full_name",
    "phone",
    "city",
    "country",
    "dob",
    "dob_day",
    "dob_month",
    "dob_year",
]

# Optional fields with empty string defaults
OPTIONAL_FIELDS = [
    "preferred_name",
    "linkedin_url",
    "portfolio_url",
    "github_url",
    "website_url",
    "postal_code",
    "province_state",
    "address",
]


def load_candidate_profile() -> Candidate:
    """
    Load candidate profile from environment variables and profile.json.

    Priority order:
    1. Environment variables (highest priority)
    2. profile.json file
    3. Raise ConfigurationError if required fields missing

    Returns:
        Candidate: Immutable candidate profile

    Raises:
        ConfigurationError: If required fields are missing
        ProfileLoadError: If profile file cannot be read
    """
    # Step 1: Load from profile.json
    profile_data = _load_profile_json()

    # Step 2: Override with environment variables
    _override_from_env(profile_data)

    # Step 3: Validate required fields
    _validate_required_fields(profile_data)

    # Step 4: Build Candidate object
    candidate = _build_candidate(profile_data)

    log.info(f"Loaded candidate profile: {candidate.full_name} ({candidate.email})")
    return candidate


def _load_profile_json() -> dict:
    """Load profile from JSON file."""
    profile_path = get_profile_path()

    if not profile_path.exists():
        # Check for example file to guide user
        example_path = get_applypilot_dir() / "profile.json.example"
        if example_path.exists():
            log.warning(f"Profile not found at {profile_path}. Copy {example_path} to {profile_path} and fill in your details.")
        else:
            log.warning(f"Profile not found at {profile_path}. Create it with your details.")
        return {}

    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            log.debug(f"Loaded profile from {profile_path}")
            return data.get("personal", data)  # Support both nested and flat formats
    except json.JSONDecodeError as e:
        raise ProfileLoadError(f"Invalid JSON in profile: {e}", str(profile_path))
    except Exception as e:
        raise ProfileLoadError(f"Failed to read profile: {e}", str(profile_path))


def _override_from_env(profile_data: dict) -> None:
    """Override profile data with environment variables."""
    env_mapping = {
        "MY_EMAIL": "email",
        "MY_EMAIL_PASSWORD": "password",
        "CANDIDATE_FULL_NAME": "full_name",
        "CANDIDATE_PREFERRED_NAME": "preferred_name",
        "CANDIDATE_PHONE": "phone",
        "CANDIDATE_CITY": "city",
        "CANDIDATE_COUNTRY": "country",
        "CANDIDATE_POSTAL_CODE": "postal_code",
        "CANDIDATE_PROVINCE_STATE": "province_state",
        "CANDIDATE_ADDRESS": "address",
        "CANDIDATE_DOB": "dob",
        "CANDIDATE_DOB_DAY": "dob_day",
        "CANDIDATE_DOB_MONTH": "dob_month",
        "CANDIDATE_DOB_YEAR": "dob_year",
        "CANDIDATE_LINKEDIN_URL": "linkedin_url",
        "CANDIDATE_PORTFOLIO_URL": "portfolio_url",
        "CANDIDATE_GITHUB_URL": "github_url",
        "CANDIDATE_WEBSITE_URL": "website_url",
    }

    for env_var, field in env_mapping.items():
        value = os.environ.get(env_var)
        if value is not None and value.strip():
            profile_data[field] = value.strip()
            log.debug(f"Override {field} from environment variable {env_var}")


def _validate_required_fields(profile_data: dict) -> None:
    """Validate that all required fields are present and non-empty."""
    missing = []
    empty = []

    for field in REQUIRED_FIELDS:
        value = profile_data.get(field)
        if value is None:
            missing.append(field)
        elif isinstance(value, str) and not value.strip():
            empty.append(field)

    if missing or empty:
        all_missing = missing + [f"{f} (empty)" for f in empty]
        raise ConfigurationError(
            f"Missing required candidate fields: {', '.join(all_missing)}. "
            f"Set them in profile.json or environment variables.",
            missing_fields=all_missing
        )


def _build_candidate(profile_data: dict) -> Candidate:
    """Build Candidate dataclass from profile data."""
    # Compute derived fields
    full_name = profile_data.get("full_name", "").strip()
    preferred_name = profile_data.get("preferred_name", "").strip()

    first_name = preferred_name or (full_name.split()[0] if full_name else "")
    last_name = full_name.split()[-1] if len(full_name.split()) > 1 else ""

    return Candidate(
        email=profile_data.get("email", "").strip(),
        password=profile_data.get("password", ""),
        full_name=full_name,
        first_name=first_name,
        last_name=last_name,
        phone=profile_data.get("phone", "").strip(),
        city=profile_data.get("city", "").strip(),
        country=profile_data.get("country", "").strip(),
        linkedin_url=profile_data.get("linkedin_url", "").strip(),
        portfolio_url=profile_data.get("portfolio_url", "").strip(),
        dob=profile_data.get("dob", "").strip(),
        dob_day=profile_data.get("dob_day", "").strip(),
        dob_month=profile_data.get("dob_month", "").strip(),
        dob_year=profile_data.get("dob_year", "").strip(),
        postal_code=profile_data.get("postal_code", "").strip(),
        province_state=profile_data.get("province_state", "").strip(),
        github_url=profile_data.get("github_url", "").strip(),
        website_url=profile_data.get("website_url", "").strip(),
        address=profile_data.get("address", "").strip(),
    )


def load_gemini_keys() -> list[str]:
    """
    Load Gemini API keys from environment variables.

    Returns:
        List of valid API keys (length > 15 chars)

    Raises:
        ConfigurationError: If no valid keys found
    """
    candidate_vars = [
        "GEMINI_API_KEY",
        "GEMINI_API_ACCESS",
        "GEMINI_API_NAME",
    ]

    keys = []
    for var in candidate_vars:
        val = os.environ.get(var, "").strip()
        if val and val not in keys and len(val) > 15:
            keys.append(val)

    # Also check for any GEMINI_* prefixed vars
    for k, v in sorted(os.environ.items()):
        val = v.strip()
        if k.startswith("GEMINI_") and val and val not in keys and len(val) > 20:
            keys.append(val)

    if not keys:
        raise ConfigurationError(
            "No Gemini API keys found in environment. "
            "Set GEMINI_API_KEY, GEMINI_API_ACCESS, or GEMINI_API_NAME."
        )

    log.info(f"Loaded {len(keys)} Gemini API key(s)")
    return keys


def get_tailored_resume_path(job: "Job") -> Path:
    """
    Resolve the tailored resume path for a job.

    Tries multiple locations in priority order.
    """
    from auto_applier_refactored.constants import get_tailored_resumes_dir

    raw_path = Path(job.tailored_resume_path)
    pdf_alt = raw_path.with_suffix(".pdf")

    candidates = [
        pdf_alt,
        get_tailored_resumes_dir() / pdf_alt.name,
        Path("tailored_resumes") / pdf_alt.name,
        Path("tailored_resumes") / "tailored_resumes" / pdf_alt.name,
        raw_path,
        get_tailored_resumes_dir() / raw_path.name,
        Path("tailored_resumes") / raw_path.name,
        get_applypilot_dir() / "resume.pdf",
        Path("resume.pdf"),
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    # Return the expected PDF path even if not found (caller will handle)
    return pdf_alt


# Avoid circular import
from auto_applier_refactored.models import Job