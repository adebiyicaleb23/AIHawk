"""
URL Resolver

Single source of truth for URL normalization and resolution.
"""

import logging
from urllib.parse import urlparse, urljoin
from typing import Optional

from auto_applier_refactored.constants import (
    WORKDAY_DOMAINS,
    GREENHOUSE_DOMAIN,
    LEVER_DOMAIN,
    LINKEDIN_DOMAIN,
)
from auto_applier_refactored.exceptions import NavigationError


logger = logging.getLogger(__name__)


def normalize_url(
    raw_url: str,
    base_url: Optional[str] = None,
    site: Optional[str] = None
) -> str:
    """
    Normalize a URL to a fully qualified HTTPS URL.

    Handles:
    - Protocol-relative URLs (//example.com)
    - www-prefixed URLs (www.example.com)
    - Relative URLs (/path/to/page)
    - Bare domains (example.com)
    - Missing scheme (example.com/path)

    Args:
        raw_url: The raw URL to normalize
        base_url: Base URL for resolving relative URLs
        site: Site name for domain inference

    Returns:
        Normalized HTTPS URL

    Raises:
        NavigationError: If URL cannot be normalized
    """
    if not raw_url or not raw_url.strip():
        raise NavigationError("Empty URL provided", url=raw_url)

    url = raw_url.strip()

    # Already has scheme
    if url.startswith("http://") or url.startswith("https://"):
        return url

    # Protocol-relative
    if url.startswith("//"):
        return "https:" + url

    # www-prefixed
    if url.startswith("www."):
        return "https://" + url

    # Relative URL
    if url.startswith("/"):
        if base_url:
            parsed_base = urlparse(base_url)
            if parsed_base.scheme and parsed_base.netloc:
                return urljoin(f"{parsed_base.scheme}://{parsed_base.netloc}", url)

        # Fallback to site domain
        site_domain = infer_site_domain(site)
        return f"https://{site_domain}{url}"

    # Bare domain or domain with path
    if not url.startswith("http"):
        site_domain = infer_site_domain(site) if site else None

        # If it looks like a domain (contains .)
        if "." in url.split("/")[0]:
            return "https://" + url

        # Last resort: use site domain
        if site_domain:
            return f"https://{site_domain}/{url}"

        raise NavigationError(f"Cannot normalize URL: {raw_url}", url=raw_url)

    return url


def infer_site_domain(site: Optional[str]) -> str:
    """
    Infer the base domain from a site name.

    Args:
        site: Site name (e.g., "Workday", "Greenhouse", "LinkedIn")

    Returns:
        Base domain (e.g., "workday.com", "greenhouse.io")
    """
    if not site:
        return "example.com"

    site_lower = site.lower()

    # Known aggregator domains
    if "talent" in site_lower:
        return "talent.com"
    if "linkedin" in site_lower:
        return LINKEDIN_DOMAIN
    if "indeed" in site_lower:
        return "indeed.com"
    if "ziprecruiter" in site_lower or "zip_recruiter" in site_lower:
        return "ziprecruiter.com"
    if "glassdoor" in site_lower:
        return "glassdoor.com"
    if "monster" in site_lower:
        return "monster.com"
    if "careerbuilder" in site_lower:
        return "careerbuilder.com"
    if "dice" in site_lower:
        return "dice.com"

    # Known ATS domains
    if "workday" in site_lower:
        return "myworkdayjobs.com"
    if "greenhouse" in site_lower:
        return GREENHOUSE_DOMAIN
    if "lever" in site_lower:
        return LEVER_DOMAIN

    # Generic: try to make a domain from the site name
    return f"{site_lower.replace(' ', '').replace('.', '')}.com"


def is_workday_url(url: str) -> bool:
    """Check if URL is a Workday portal."""
    return any(domain in url for domain in WORKDAY_DOMAINS)


def is_greenhouse_url(url: str) -> bool:
    """Check if URL is a Greenhouse portal."""
    return GREENHOUSE_DOMAIN in url


def is_lever_url(url: str) -> bool:
    """Check if URL is a Lever portal."""
    return LEVER_DOMAIN in url


def is_linkedin_url(url: str) -> bool:
    """Check if URL is a LinkedIn portal."""
    return LINKEDIN_DOMAIN in url


def build_workday_login_url(job_url: str) -> list[str]:
    """
    Build possible login URLs for a Workday tenant.

    Args:
        job_url: The job page URL

    Returns:
        List of possible login URLs to try
    """
    parsed = urlparse(job_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    from auto_applier_refactored.constants import WORKDAY_SELECTORS
    return [f"{base_url}{path}" for path in WORKDAY_SELECTORS["login_page_patterns"]]


def extract_workday_job_id(url: str) -> Optional[str]:
    """Extract job ID from Workday URL."""
    import re
    match = re.search(r'/job/([^/?]+)', url)
    return match.group(1) if match else None


def build_workday_apply_urls(job_url: str) -> list[str]:
    """
    Build possible apply URLs for a Workday job.

    Args:
        job_url: The job page URL

    Returns:
        List of possible apply URLs
    """
    import re

    urls = []
    job_id = extract_workday_job_id(job_url)

    # Common patterns
    urls.append(job_url + "/apply")
    urls.append(job_url.replace("/job/", "/apply/"))
    urls.append(job_url.replace("External_Career_Site/job", "External_Career_Site/apply"))
    urls.append(job_url.replace("/job/", "/apply/job/"))
    urls.append(job_url.split("?")[0] + "/apply")

    if job_id:
        base = job_url.split("/job/")[0]
        urls.extend([
            f"{base}/apply/{job_id}",
            f"{base}/apply/job/{job_id}",
        ])

    return urls