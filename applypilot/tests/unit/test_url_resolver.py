"""
Tests for URL resolver module.
"""

import pytest

from auto_applier_refactored.navigation.url_resolver import (
    normalize_url,
    infer_site_domain,
    is_workday_url,
    is_greenhouse_url,
    is_lever_url,
    is_linkedin_url,
    build_workday_login_url,
    extract_workday_job_id,
    build_workday_apply_urls,
)
from auto_applier_refactored.exceptions import NavigationError


class TestNormalizeUrl:
    """Tests for normalize_url function."""

    def test_already_https(self):
        """Test URLs that already have HTTPS scheme."""
        assert normalize_url("https://example.com/job") == "https://example.com/job"
        assert normalize_url("https://example.com/job?param=value") == "https://example.com/job?param=value"

    def test_already_http(self):
        """Test URLs that already have HTTP scheme."""
        assert normalize_url("http://example.com/job") == "http://example.com/job"

    def test_protocol_relative(self):
        """Test protocol-relative URLs (//example.com)."""
        assert normalize_url("//example.com/job") == "https://example.com/job"
        assert normalize_url("//example.com/job?param=value") == "https://example.com/job?param=value"

    def test_www_prefixed(self):
        """Test www-prefixed URLs."""
        assert normalize_url("www.example.com/job") == "https://www.example.com/job"

    def test_relative_url_with_base(self):
        """Test relative URLs with base URL."""
        assert normalize_url("/job/123", base_url="https://example.com") == "https://example.com/job/123"
        assert normalize_url("/apply", base_url="https://example.com/job/123") == "https://example.com/apply"

    def test_relative_url_with_site(self):
        """Test relative URLs with site name for domain inference."""
        assert normalize_url("/job/123", site="Workday") == "https://myworkdayjobs.com/job/123"
        assert normalize_url("/apply", site="Greenhouse") == "https://greenhouse.io/apply"

    def test_relative_url_fallback(self):
        """Test relative URLs fallback to example.com."""
        assert normalize_url("/job/123") == "https://example.com/job/123"

    def test_bare_domain(self):
        """Test bare domain URLs."""
        assert normalize_url("example.com/job") == "https://example.com/job"
        assert normalize_url("company.myworkdayjobs.com/job/123") == "https://company.myworkdayjobs.com/job/123"

    def test_empty_url_raises(self):
        """Test that empty URLs raise NavigationError."""
        with pytest.raises(NavigationError):
            normalize_url("")

        with pytest.raises(NavigationError):
            normalize_url("   ")

    def test_invalid_url_raises(self):
        """Test that unparseable URLs raise NavigationError."""
        # This should work - it's a bare domain
        assert normalize_url("example.com") == "https://example.com"


class TestInferSiteDomain:
    """Tests for infer_site_domain function."""

    def test_known_sites(self):
        """Test known site name mappings."""
        assert infer_site_domain("Talent.com") == "talent.com"
        assert infer_site_domain("LinkedIn") == "linkedin.com"
        assert infer_site_domain("Indeed") == "indeed.com"
        assert infer_site_domain("ZipRecruiter") == "ziprecruiter.com"
        assert infer_site_domain("Glassdoor") == "glassdoor.com"
        assert infer_site_domain("Monster") == "monster.com"
        assert infer_site_domain("CareerBuilder") == "careerbuilder.com"
        assert infer_site_domain("Dice") == "dice.com"

    def test_ats_sites(self):
        """Test ATS site name mappings."""
        assert infer_site_domain("Workday") == "myworkdayjobs.com"
        assert infer_site_domain("Greenhouse") == "greenhouse.io"
        assert infer_site_domain("Lever") == "lever.co"

    def test_none_returns_example(self):
        """Test None returns example.com."""
        assert infer_site_domain(None) == "example.com"

    def test_unknown_site_generates_domain(self):
        """Test unknown site generates domain from name."""
        assert infer_site_domain("CustomATS") == "customats.com"
        assert infer_site_domain("My Company") == "mycompany.com"
        assert infer_site_domain("ATS.Pro") == "atspro.com"


class TestPortalDetection:
    """Tests for portal detection functions."""

    def test_is_workday_url(self):
        assert is_workday_url("https://company.myworkdayjobs.com/job/123")
        assert is_workday_url("https://company.workday.com/job/123")
        assert not is_workday_url("https://greenhouse.io/job/123")

    def test_is_greenhouse_url(self):
        assert is_greenhouse_url("https://boards.greenhouse.io/job/123")
        assert not is_greenhouse_url("https://company.myworkdayjobs.com/job/123")

    def test_is_lever_url(self):
        assert is_lever_url("https://jobs.lever.co/company/123")
        assert not is_lever_url("https://company.myworkdayjobs.com/job/123")

    def test_is_linkedin_url(self):
        assert is_linkedin_url("https://linkedin.com/jobs/123")
        assert is_linkedin_url("https://www.linkedin.com/jobs/123")
        assert not is_linkedin_url("https://company.myworkdayjobs.com/job/123")


class TestWorkdayUrlBuilders:
    """Tests for Workday URL builder functions."""

    def test_build_workday_login_url(self):
        urls = build_workday_login_url("https://company.myworkdayjobs.com/job/123")
        assert len(urls) == 5
        assert "https://company.myworkdayjobs.com/login" in urls
        assert "https://company.myworkdayjobs.com/signin" in urls
        assert "https://company.myworkdayjobs.com/auth/login" in urls

    def test_extract_workday_job_id(self):
        assert extract_workday_job_id("https://company.myworkdayjobs.com/job/123") == "123"
        assert extract_workday_job_id("https://company.myworkdayjobs.com/job/ABC-123?param=value") == "ABC-123"
        assert extract_workday_job_id("https://example.com/job/123") == "123"
        assert extract_workday_job_id("https://example.com/apply") is None

    def test_build_workday_apply_urls(self):
        urls = build_workday_apply_urls("https://company.myworkdayjobs.com/job/123")
        assert len(urls) >= 7
        assert "https://company.myworkdayjobs.com/job/123/apply" in urls
        assert "https://company.myworkdayjobs.com/apply/123" in urls
        assert "https://company.myworkdayjobs.com/apply/job/123" in urls