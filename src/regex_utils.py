"""
Regex utilities for ApplyPilot - adapted from Auto_Jobs_Applier_AI_Agent
Generates regex patterns for blacklisting.
"""

import re
from typing import List


def generate_regex_patterns_for_blacklisting(blacklist: List[str]) -> List[str]:
    """
    Convert blacklist terms into regex patterns using positive lookaheads.

    Each term is split into words and patterns are created to match all words
    in any order. For example, "Data Engineer" becomes:
    (?=.*\\bData\\b)(?=.*\\bEngineer\\b)

    Args:
        blacklist: List of blacklist terms (strings)

    Returns:
        List of regex pattern strings
    """
    patterns = []

    for term in blacklist:
        if not term or not term.strip():
            continue

        # Split term into words
        words = term.strip().split()

        if not words:
            continue

        # Build positive lookahead pattern for each word
        # This matches all words in any order
        pattern_parts = []
        for word in words:
            # Escape special regex characters
            escaped_word = re.escape(word)
            pattern_parts.append(f"(?=.*\\b{escaped_word}\\b)")

        # Combine all lookaheads
        full_pattern = "".join(pattern_parts)
        patterns.append(full_pattern)

    return patterns


def is_blacklisted(text: str, patterns: List[str]) -> bool:
    """
    Check if text matches any blacklist pattern.

    Args:
        text: Text to check
        patterns: List of regex patterns from generate_regex_patterns_for_blacklisting

    Returns:
        True if blacklisted, False otherwise
    """
    if not text or not patterns:
        return False

    text_lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False