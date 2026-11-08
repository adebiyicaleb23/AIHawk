"""
Tests for models module.
"""

import pytest
from datetime import datetime
from pathlib import Path

from auto_applier_refactored.models import (
    Candidate,
    Job,
    ApplicationResult,
    ApplicationStatus,
    AutoApplySummary,
)


class TestCandidate:
    """Tests for Candidate dataclass."""

    def test_creation(self):
        """Test basic Candidate creation."""
        candidate = Candidate(
            email="test@example.com",
            password="secret",
            full_name="Test User",
            first_name="Test",
            last_name="User",
            phone="+1234567890",
            city="Test City",
            country="Test Country",
            linkedin_url="https://linkedin.com/in/test",
            portfolio_url="https://portfolio.com",
            dob="01/01/1990",
            dob_day="01",
            dob_month="01",
            dob_year="1990",
        )

        assert candidate.email == "test@example.com"
        assert candidate.first_name == "Test"
        assert candidate.last_name == "User"

    def test_immutability(self):
        """Test that Candidate is frozen/immutable."""
        candidate = Candidate(
            email="test@example.com",
            password="secret",
            full_name="Test User",
            first_name="Test",
            last_name="User",
            phone="+1234567890",
            city="Test City",
            country="Test Country",
            linkedin_url="",
            portfolio_url="",
            dob="01/01/1990",
            dob_day="01",
            dob_month="01",
            dob_year="1990",
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            candidate.email = "new@example.com"

    def test_name_parts_property(self):
        """Test name_parts property returns tuple."""
        candidate = Candidate(
            email="test@example.com",
            password="secret",
            full_name="Test User",
            first_name="Test",
            last_name="User",
            phone="+1234567890",
            city="Test City",
            country="Test Country",
            linkedin_url="",
            portfolio_url="",
            dob="01/01/1990",
            dob_day="01",
            dob_month="01",
            dob_year="1990",
        )

        first, last = candidate.name_parts
        assert first == "Test"
        assert last == "User"

    def test_optional_fields_default_empty(self):
        """Test optional fields default to empty strings."""
        candidate = Candidate(
            email="test@example.com",
            password="secret",
            full_name="Test User",
            first_name="Test",
            last_name="User",
            phone="+1234567890",
            city="Test City",
            country="Test Country",
            linkedin_url="",
            portfolio_url="",
            dob="01/01/1990",
            dob_day="01",
            dob_month="01",
            dob_year="1990",
        )

        assert candidate.postal_code == ""
        assert candidate.province_state == ""
        assert candidate.github_url == ""
        assert candidate.website_url == ""
        assert candidate.address == ""


class TestJob:
    """Tests for Job dataclass."""

    def test_creation(self):
        """Test basic Job creation."""
        job = Job(
            url="https://example.com/job/123",
            title="AI Trainer",
            site="Workday",
            application_url="https://example.com/job/123/apply",
            tailored_resume_path=Path("resume.pdf"),
            fit_score=8,
            apply_status=None,
        )

        assert job.url == "https://example.com/job/123"
        assert job.title == "AI Trainer"
        assert job.fit_score == 8

    def test_is_tailored_property(self):
        """Test is_tailored property."""
        job_with_resume = Job(
            url="https://example.com/job/123",
            title="AI Trainer",
            site="Workday",
            application_url="https://example.com/job/123/apply",
            tailored_resume_path=Path("resume.pdf"),
            fit_score=8,
            apply_status=None,
        )

        job_without_resume = Job(
            url="https://example.com/job/456",
            title="AI Trainer",
            site="Workday",
            application_url="https://example.com/job/456/apply",
            tailored_resume_path=Path(""),
            fit_score=8,
            apply_status=None,
        )

        assert job_with_resume.is_tailored is True
        assert job_without_resume.is_tailored is False

    def test_is_applied_property(self):
        """Test is_applied property."""
        job_applied = Job(
            url="https://example.com/job/123",
            title="AI Trainer",
            site="Workday",
            application_url="https://example.com/job/123/apply",
            tailored_resume_path=Path("resume.pdf"),
            fit_score=8,
            apply_status="applied",
        )

        job_not_applied = Job(
            url="https://example.com/job/456",
            title="AI Trainer",
            site="Workday",
            application_url="https://example.com/job/456/apply",
            tailored_resume_path=Path("resume.pdf"),
            fit_score=8,
            apply_status="ready_to_apply",
        )

        assert job_applied.is_applied is True
        assert job_not_applied.is_applied is False


class TestApplicationResult:
    """Tests for ApplicationResult dataclass."""

    def test_creation(self):
        """Test basic ApplicationResult creation."""
        result = ApplicationResult(
            job_url="https://example.com/job/123",
            status=ApplicationStatus.APPLIED,
            error_message=None,
            applied_at=datetime.now(),
            duration_ms=5000,
        )

        assert result.job_url == "https://example.com/job/123"
        assert result.status == ApplicationStatus.APPLIED

    def test_is_success(self):
        """Test is_success method."""
        success = ApplicationResult(
            job_url="https://example.com/job/123",
            status=ApplicationStatus.APPLIED,
        )

        ready = ApplicationResult(
            job_url="https://example.com/job/123",
            status=ApplicationStatus.READY_TO_APPLY,
        )

        error = ApplicationResult(
            job_url="https://example.com/job/123",
            status=ApplicationStatus.ERROR,
        )

        assert success.is_success() is True
        assert ready.is_success() is False
        assert error.is_success() is False

    def test_is_ready(self):
        """Test is_ready method."""
        ready = ApplicationResult(
            job_url="https://example.com/job/123",
            status=ApplicationStatus.READY_TO_APPLY,
        )

        applied = ApplicationResult(
            job_url="https://example.com/job/123",
            status=ApplicationStatus.APPLIED,
        )

        assert ready.is_ready() is True
        assert applied.is_ready() is False


class TestAutoApplySummary:
    """Tests for AutoApplySummary dataclass."""

    def test_success_rate(self):
        """Test success_rate property."""
        summary = AutoApplySummary(applied=5, ready=3, total=10, errors=2)
        assert summary.success_rate == 0.5

    def test_success_rate_zero_total(self):
        """Test success_rate with zero total."""
        summary = AutoApplySummary(applied=0, ready=0, total=0, errors=0)
        assert summary.success_rate == 0.0


class TestApplicationStatus:
    """Tests for ApplicationStatus enum."""

    def test_values(self):
        """Test enum values."""
        assert ApplicationStatus.APPLIED.value == "applied"
        assert ApplicationStatus.READY_TO_APPLY.value == "ready_to_apply"
        assert ApplicationStatus.PORTAL_GATED.value == "portal_gated"
        assert ApplicationStatus.ERROR.value == "error"