"""
Tests for config module.
"""

import pytest
import os
from pathlib import Path

from auto_applier_refactored.config import load_candidate_profile, load_gemini_keys
from auto_applier_refactored.models import Candidate
from auto_applier_refactored.exceptions import ConfigurationError, ProfileLoadError


class TestLoadCandidateProfile:
    """Tests for load_candidate_profile function."""

    def test_load_from_env_vars(self, mock_env_vars, temp_profile_json):
        """Test loading candidate from environment variables."""
        candidate = load_candidate_profile()

        assert isinstance(candidate, Candidate)
        assert candidate.email == "test@example.com"
        assert candidate.password == "testpass123"
        assert candidate.full_name == "Test User"
        assert candidate.first_name == "Test"
        assert candidate.last_name == "User"

    def test_load_from_profile_json(self, temp_profile_json, monkeypatch):
        """Test loading candidate from profile.json."""
        # Remove env vars to test profile.json loading
        monkeypatch.delenv("MY_EMAIL", raising=False)
        monkeypatch.delenv("MY_EMAIL_PASSWORD", raising=False)

        candidate = load_candidate_profile()

        assert candidate.email == "test@example.com"
        assert candidate.password == "testpass123"
        assert candidate.full_name == "Test User"

    def test_env_overrides_profile(self, temp_profile_json, mock_env_vars):
        """Test that environment variables override profile.json."""
        candidate = load_candidate_profile()

        # Env vars should take precedence
        assert candidate.email == "test@example.com"
        assert candidate.password == "testpass123"

    def test_missing_required_field_raises(self, monkeypatch, tmp_path, temp_profile_json):
        """Test that missing required fields raise ConfigurationError."""
        # Remove all env vars
        for var in ["MY_EMAIL", "MY_EMAIL_PASSWORD", "GEMINI_API_KEY", "GEMINI_API_ACCESS", "GEMINI_API_NAME"]:
            monkeypatch.delenv(var, raising=False)

        # Create incomplete profile
        profile_path = tmp_path / "profile.json"
        import json
        with open(profile_path, "w") as f:
            json.dump({"personal": {"email": "test@example.com"}}, f)  # Missing password, name, etc.

        import auto_applier_refactored.config as config_module
        monkeypatch.setattr(config_module, "get_profile_path", lambda: profile_path)

        with pytest.raises(ConfigurationError) as exc_info:
            load_candidate_profile()

        assert "Missing required candidate fields" in str(exc_info.value)
        assert exc_info.value.missing_fields is not None

    def test_empty_required_field_raises(self, monkeypatch, tmp_path, temp_profile_json):
        """Test that empty required fields raise ConfigurationError."""
        for var in ["MY_EMAIL", "MY_EMAIL_PASSWORD", "GEMINI_API_KEY", "GEMINI_API_ACCESS", "GEMINI_API_NAME"]:
            monkeypatch.delenv(var, raising=False)

        profile_path = tmp_path / "profile.json"
        import json
        with open(profile_path, "w") as f:
            json.dump({"personal": {"email": "", "password": "pass", "full_name": "Test"}}, f)

        import auto_applier_refactored.config as config_module
        monkeypatch.setattr(config_module, "get_profile_path", lambda: profile_path)

        with pytest.raises(ConfigurationError) as exc_info:
            load_candidate_profile()

        assert "email (empty)" in str(exc_info.value)

    def test_first_name_from_preferred_name(self, temp_profile_json, monkeypatch):
        """Test first_name is derived from preferred_name."""
        monkeypatch.delenv("MY_EMAIL", raising=False)
        monkeypatch.delenv("MY_EMAIL_PASSWORD", raising=False)

        candidate = load_candidate_profile()
        assert candidate.first_name == "Test"  # From preferred_name

    def test_first_name_fallback_to_full_name(self, monkeypatch, tmp_path, temp_profile_json):
        """Test first_name falls back to first part of full_name."""
        for var in ["MY_EMAIL", "MY_EMAIL_PASSWORD", "GEMINI_API_KEY", "GEMINI_API_ACCESS", "GEMINI_API_NAME"]:
            monkeypatch.delenv(var, raising=False)

        profile_path = tmp_path / "profile.json"
        import json
        with open(profile_path, "w") as f:
            json.dump({
                "personal": {
                    "full_name": "John Doe",
                    "email": "john@example.com",
                    "password": "pass",
                    "phone": "+123",
                    "city": "City",
                    "country": "Country",
                    "dob": "01/01/1990",
                    "dob_day": "01",
                    "dob_month": "01",
                    "dob_year": "1990",
                }
            }, f)

        import auto_applier_refactored.config as config_module
        monkeypatch.setattr(config_module, "get_profile_path", lambda: profile_path)

        candidate = load_candidate_profile()
        assert candidate.first_name == "John"
        assert candidate.last_name == "Doe"


class TestLoadGeminiKeys:
    """Tests for load_gemini_keys function."""

    def test_load_from_env_vars(self, mock_env_vars):
        """Test loading Gemini keys from environment variables."""
        keys = load_gemini_keys()

        assert isinstance(keys, list)
        assert len(keys) >= 2  # GEMINI_API_KEY and GEMINI_API_ACCESS
        assert all(len(k) > 15 for k in keys)

    def test_no_keys_raises(self, monkeypatch):
        """Test that missing keys raise ConfigurationError."""
        for var in ["GEMINI_API_KEY", "GEMINI_API_ACCESS", "GEMINI_API_NAME"]:
            monkeypatch.delenv(var, raising=False)

        # Also remove any GEMINI_* prefixed vars
        for k in list(os.environ.keys()):
            if k.startswith("GEMINI_"):
                monkeypatch.delenv(k, raising=False)

        with pytest.raises(ConfigurationError) as exc_info:
            load_gemini_keys()

        assert "No Gemini API keys found" in str(exc_info.value)

    def test_deduplication(self, monkeypatch):
        """Test that duplicate keys are deduplicated."""
        monkeypatch.setenv("GEMINI_API_KEY", "same_key_12345678901234567890")
        monkeypatch.setenv("GEMINI_API_ACCESS", "same_key_12345678901234567890")
        monkeypatch.setenv("GEMINI_API_NAME", "different_key_12345678901234567890")

        keys = load_gemini_keys()

        # Should only have 2 unique keys
        assert len(keys) == 2


class TestCandidateModel:
    """Tests for Candidate dataclass."""

    def test_immutability(self, sample_candidate):
        """Test that Candidate is immutable (frozen)."""
        with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
            sample_candidate.email = "new@example.com"

    def test_name_parts_property(self, sample_candidate):
        """Test name_parts property."""
        first, last = sample_candidate.name_parts
        assert first == "Test"
        assert last == "User"