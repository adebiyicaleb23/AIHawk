"""
Form Filler

Fills application forms using candidate data and Gemini for screening questions.
"""

import logging
from typing import Optional
from playwright.sync_api import Page, ElementHandle

from auto_applier_refactored.models import Candidate
from auto_applier_refactored.forms.field_mapper import FieldMapping, build_field_mappings
from auto_applier_refactored.gemini_client import GeminiClient
from auto_applier_refactored.constants import AFFIRMATIVE_KEYWORDS


class FormFiller:
    """Fills application forms with candidate data."""

    def __init__(self, candidate: Candidate, gemini_client: Optional[GeminiClient] = None, portal: str = "generic"):
        self.candidate = candidate
        self.gemini = gemini_client
        self.portal = portal
        self.logger = logging.getLogger(__name__)
        self.mappings = build_field_mappings(candidate, portal)

    def fill(self, page: Page) -> None:
        """Fill all mapped fields on the page."""
        # Fill standard fields
        for mapping in self.mappings:
            if mapping.value:
                self._fill_field(page, mapping)

        # Fill screening questions
        self._fill_screening_questions(page)

        # Check affirmative checkboxes/radios
        self._check_affirmative_inputs(page)

    def _fill_field(self, page: Page, mapping: FieldMapping) -> bool:
        """Fill a single field using its selectors."""
        for sel in mapping.selectors:
            try:
                els = page.query_selector_all(sel)
                for el in els:
                    if el.is_visible() and not el.input_value():
                        el.fill(mapping.value)
                        self._safe_log(f"  Filled {mapping.label or sel}")
                        return True
            except Exception as e:
                self._safe_log(f"  Error filling {mapping.label or sel}: {e}")
                continue
        return False

    def _fill_screening_questions(self, page: Page) -> None:
        """Fill screening questions using Gemini."""
        if not self.gemini:
            return

        for inp in page.query_selector_all("textarea, input[type='text']:not([readonly])"):
            try:
                if not inp.is_visible() or inp.input_value():
                    continue

                label_text = self._get_field_label(page, inp)
                if label_text and len(label_text.strip()) > 3:
                    answer = self.gemini.answer_question(label_text, self.candidate)
                    inp.fill(answer)
                    self._safe_log(f"  Answered screening question: {label_text[:50]}...")
            except Exception as e:
                self._safe_log(f"  Error filling screening question: {e}")

    def _get_field_label(self, page: Page, inp: ElementHandle) -> str:
        """Extract label text for an input element."""
        inp_id = inp.get_attribute("id")
        if inp_id:
            lbl = page.query_selector(f"label[for='{inp_id}']")
            if lbl:
                return lbl.inner_text()

        return (
            inp.get_attribute("placeholder")
            or inp.get_attribute("aria-label")
            or inp.get_attribute("name")
            or ""
        )

    def _check_affirmative_inputs(self, page: Page) -> None:
        """Check affirmative checkboxes and radio buttons."""
        for inp in page.query_selector_all("input[type='radio'], input[type='checkbox']"):
            try:
                if inp.is_checked():
                    continue

                parent = inp.evaluate_handle("el => el.closest('label') || el.parentElement")
                txt = (parent.as_element().inner_text() if parent and parent.as_element() else "").lower()

                if any(word in txt for word in AFFIRMATIVE_KEYWORDS):
                    inp.check(force=True)
                    self._safe_log(f"  Checked affirmative input: {txt[:50]}")
            except Exception:
                pass

    def _safe_log(self, msg: str) -> None:
        """Log message with safe ASCII encoding."""
        safe_msg = msg.encode('ascii', 'replace').decode('ascii')
        self.logger.info(safe_msg)