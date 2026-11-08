"""
Pytest Configuration and Fixtures

Provides common fixtures for unit and integration tests.
"""

import pytest
from unittest.mock import MagicMock, patch
from playwright.sync_api import Page, Frame, ElementHandle
from pathlib import Path

from auto_applier_refactored.models import Candidate, Job, ApplicationStatus, ApplicationResult
from auto_applier_refactored.constants import WORKDAY_SELECTORS, GENERIC_SELECTORS


@pytest.fixture
def mock_page():
    """Create a mock Playwright page."""
    page = MagicMock(spec=Page)
    page.url = "https://example.com"
    return page


@pytest.fixture
def mock_frame():
    """Create a mock Playwright frame."""
    frame = MagicMock(spec=Frame)
    frame.url = "https://example.com/iframe"
    return frame


@pytest.fixture
def mock_element():
    """Create a mock Playwright element."""
    element = MagicMock(spec=ElementHandle)
    element.is_visible.return_value = True
    element.input_value.return_value = ""
    return element


@pytest.fixture
def sample_candidate():
    """Create a sample candidate for testing."""
    return Candidate(
        email="test@example.com",
        password="secret123",
        full_name="Test User",
        first_name="Test",
        last_name="User",
        phone="+1234567890",
        city="Test City",
        country="Test Country",
        linkedin_url="https://linkedin.com/in/testuser",
        portfolio_url="https://portfolio.example.com",
        dob="01/01/1990",
        dob_day="01",
        dob_month="01",
        dob_year="1990",
        postal_code="12345",
        province_state="Test State",
        github_url="https://github.com/testuser",
        website_url="https://testuser.example.com",
        address="123 Test St",
    )


@pytest.fixture
def sample_job():
    """Create a sample job for testing."""
    return Job(
        url="https://example.com/job/123",
        title="AI Trainer",
        site="Workday",
        application_url="https://example.com/job/123/apply",
        tailored_resume_path=Path("tailored_resumes/resume_123.pdf"),
        fit_score=9,
        apply_status=None,
    )


@pytest.fixture
def sample_job_workday():
    """Create a sample Workday job."""
    return Job(
        url="https://company.myworkdayjobs.com/job/123",
        title="AI Data Evaluator",
        site="Workday",
        application_url="https://company.myworkdayjobs.com/job/123/apply",
        tailored_resume_path=Path("tailored_resumes/resume_123.pdf"),
        fit_score=8,
        apply_status=None,
    )


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset any singleton state between tests."""
    yield
    # Cleanup if needed


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("MY_EMAIL", "test@example.com")
    monkeypatch.setenv("MY_EMAIL_PASSWORD", "testpass123")
    monkeypatch.setenv("GEMINI_API_KEY", "test_key_12345678901234567890")
    monkeypatch.setenv("GEMINI_API_ACCESS", "test_key_09876543210987654321")


@pytest.fixture
def temp_profile_json(tmp_path, monkeypatch):
    """Create a temporary profile.json for testing."""
    profile_data = {
        "personal": {
            "full_name": "Test User",
            "preferred_name": "Test",
            "email": "test@example.com",
            "password": "testpass123",
            "phone": "+1234567890",
            "city": "Test City",
            "province_state": "Test State",
            "country": "Test Country",
            "postal_code": "12345",
            "address": "123 Test St",
            "dob_day": "01",
            "dob_month": "01",
            "dob_year": "1990",
            "dob": "01/01/1990",
            "linkedin_url": "https://linkedin.com/in/testuser",
            "github_url": "https://github.com/testuser",
            "portfolio_url": "https://portfolio.example.com",
            "website_url": "https://testuser.example.com",
        }
    }
    profile_path = tmp_path / "profile.json"
    import json
    with open(profile_path, "w") as f:
        json.dump(profile_data, f)

    # Patch the profile path in config module where it's used
    import auto_applier_refactored.config as config_module

    def mock_get_profile_path():
        return profile_path

    monkeypatch.setattr(config_module, "get_profile_path", mock_get_profile_path)
    yield profile_path