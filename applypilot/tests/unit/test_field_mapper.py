"""
Tests for field_mapper module.
"""

import pytest

from auto_applier_refactored.forms.field_mapper import build_field_mappings, FieldMapping
from auto_applier_refactored.models import Candidate


class TestBuildFieldMappings:
    """Tests for build_field_mappings function."""

    @pytest.fixture
    def candidate(self):
        return Candidate(
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
            postal_code="12345",
            province_state="Test State",
            github_url="https://github.com/test",
            website_url="https://test.com",
            address="123 Test St",
        )

    def test_generic_portal_mappings(self, candidate):
        """Test field mappings for generic portal."""
        mappings = build_field_mappings(candidate, portal="generic")

        assert len(mappings) > 0
        assert all(isinstance(m, FieldMapping) for m in mappings)

        # Check email mapping exists
        email_mappings = [m for m in mappings if m.label == "email"]
        assert len(email_mappings) == 1
        assert email_mappings[0].value == "test@example.com"

        # Check name mappings
        first_name_mappings = [m for m in mappings if m.label == "first name"]
        assert len(first_name_mappings) >= 1
        assert first_name_mappings[0].value == "Test"

        last_name_mappings = [m for m in mappings if m.label == "last name"]
        assert len(last_name_mappings) >= 1
        assert last_name_mappings[0].value == "User"

    def test_workday_portal_mappings(self, candidate):
        """Test field mappings for Workday portal."""
        mappings = build_field_mappings(candidate, portal="workday")

        # Should have Workday-specific mappings
        workday_mappings = [m for m in mappings if m.label.startswith("Workday")]
        assert len(workday_mappings) > 0

        # Check Workday firstName mapping
        first_name_wd = [m for m in workday_mappings if "firstName" in m.label]
        assert len(first_name_wd) >= 1

    def test_empty_values_excluded(self, candidate):
        """Test that empty values are excluded from mappings."""
        candidate_empty = Candidate(
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

        mappings = build_field_mappings(candidate_empty, portal="generic")

        # LinkedIn and portfolio should not be in mappings since they're empty
        linkedin_mappings = [m for m in mappings if "linkedin" in m.label.lower()]
        portfolio_mappings = [m for m in mappings if "portfolio" in m.label.lower()]

        assert len(linkedin_mappings) == 0
        assert len(portfolio_mappings) == 0

    def test_field_mapping_structure(self, candidate):
        """Test FieldMapping structure."""
        mappings = build_field_mappings(candidate, portal="generic")
        mapping = mappings[0]

        assert hasattr(mapping, "selectors")
        assert hasattr(mapping, "value")
        assert hasattr(mapping, "label")
        assert isinstance(mapping.selectors, list)
        assert isinstance(mapping.value, str)
        assert isinstance(mapping.label, str)