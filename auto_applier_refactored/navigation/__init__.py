"""Navigation utilities for job application pages."""

from auto_applier_refactored.navigation.url_resolver import normalize_url, infer_site_domain
from auto_applier_refactored.navigation.page_navigator import PageNavigator
from auto_applier_refactored.navigation.apply_button_finder import find_and_click_apply

__all__ = [
    "normalize_url",
    "infer_site_domain",
    "PageNavigator",
    "find_and_click_apply",
]