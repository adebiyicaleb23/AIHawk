"""
Gemini Client

Handles Gemini API calls with automatic key rotation on rate limits.
"""

import logging
import time
import httpx
from typing import Optional, List

from auto_applier_refactored.models import Candidate
from auto_applier_refactored.exceptions import GeminiError
from auto_applier_refactored.constants import (
    GEMINI_MODEL,
    GEMINI_NATIVE_BASE,
    GEMINI_REQUEST_TIMEOUT,
)

logger = logging.getLogger(__name__)


class GeminiClient:
    """Gemini API client with automatic key rotation."""

    def __init__(self, api_keys: List[str]):
        """
        Initialize Gemini client.

        Args:
            api_keys: List of Gemini API keys
        """
        if not api_keys:
            raise ValueError("At least one API key required")

        self.keys = api_keys
        self.current_key_index = 0
        self.client = httpx.Client(timeout=GEMINI_REQUEST_TIMEOUT)

    def answer_question(self, question_text: str, candidate: Candidate) -> str:
        """
        Answer a screening question using Gemini.

        Args:
            question_text: The question to answer
            candidate: Candidate profile for context

        Returns:
            Answer string or fallback
        """
        prompt = self._build_prompt(question_text, candidate)

        for attempt in range(len(self.keys)):
            key = self.keys[self.current_key_index]
            try:
                return self._call_gemini(prompt, key)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Rate limited - rotate key
                    logger.warning(
                        f"Gemini rate limited (key #{self.current_key_index + 1}), rotating..."
                    )
                    self._rotate_key()
                    continue
                elif e.response.status_code == 403:
                    # Forbidden - try next key
                    logger.warning(f"Gemini key #{self.current_key_index + 1} forbidden, rotating...")
                    self._rotate_key()
                    continue
                raise
            except httpx.TimeoutException:
                logger.warning(f"Gemini request timed out (key #{self.current_key_index + 1})")
                self._rotate_key()
                continue
            except Exception as e:
                logger.warning(f"Gemini error (key #{self.current_key_index + 1}): {e}")
                self._rotate_key()
                continue

        # All keys exhausted - return fallback
        logger.warning("All Gemini keys exhausted, returning fallback answer")
        return "Yes"

    def _rotate_key(self) -> None:
        """Rotate to next API key."""
        self.current_key_index = (self.current_key_index + 1) % len(self.keys)
        logger.info(f"Rotated to Gemini key #{self.current_key_index + 1}")

    def _build_prompt(self, question_text: str, candidate: Candidate) -> str:
        """Build the prompt for Gemini."""
        return f"""You are answering a job application screening question for this candidate:
- Name: {candidate.full_name}
- Email: {candidate.email}
- Phone: {candidate.phone}
- Location: {candidate.city}, {candidate.country} (Remote work, authorized for international remote contracts)
- Experience: 5 years — AI Evaluation, Data Annotation, RLHF, Virtual Assistance, Administration
- Education: Master's degree
- DOB: {candidate.dob}
- Notice period: Available immediately
- Remote: Yes

Question: {question_text}

Reply with ONLY the direct concise answer for a form field (e.g. 'Yes', '5', 'Immediately', a 1-sentence answer, or a number). No explanation."""

    def _call_gemini(self, prompt: str, api_key: str) -> str:
        """Call the native Gemini generateContent API."""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 100,
            },
        }

        url = f"{GEMINI_NATIVE_BASE}/models/{GEMINI_MODEL}:generateContent"
        resp = self.client.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            params={"key": api_key},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False