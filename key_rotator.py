#!/usr/bin/env python3
"""
ApplyPilot Key Rotator
----------------------
Patches ApplyPilot's LLM client to rotate between multiple Gemini API keys
when one gets rate-limited (HTTP 429). Then delegates to ApplyPilot's real CLI.

Usage (same as applypilot CLI):
    python key_rotator.py run --min-score 5 --validation lenient

Keys are picked up automatically from environment variables:
    GEMINI_API_KEY    — primary key (required)
    GEMINI_API_KEY_2  — secondary key (optional)
    GEMINI_API_KEY_3  — tertiary key (optional)
    ... and so on
"""
import os
import sys
import httpx
import applypilot.llm as llm_mod

# ── Collect all Gemini keys from environment ────────────────────────────────
candidate_vars = ["GEMINI_API_KEY", "GEMINI_API_ACCESS", "GEMINI_API_NAME"]
keys = []
for var in candidate_vars:
    val = os.environ.get(var, "").strip()
    if val and val not in keys:
        keys.append(val)

# Also check any other GEMINI_* vars that might be keys
for k, v in sorted(os.environ.items()):
    val = v.strip()
    if k.startswith("GEMINI_") and val and val not in keys and len(val) > 20:
        keys.append(val)

if not keys:
    print("[KeyRotator] ERROR: No GEMINI_API_KEY found in environment.", flush=True)
    sys.exit(1)

# ── Patch LLMClient only if we have more than one key ────────────────────────
if len(keys) > 1:
    _orig_chat = llm_mod.LLMClient.chat

    def _rotating_chat(self, messages, temperature=0.0, max_tokens=4096):
        last_exc = None
        for i, key in enumerate(keys):
            self.api_key = key
            try:
                return _orig_chat(self, messages, temperature, max_tokens)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429 and i < len(keys) - 1:
                    print(
                        f"[KeyRotator] Key {i + 1} rate-limited (429) "
                        f"→ switching to key {i + 2}",
                        flush=True,
                    )
                    last_exc = exc
                    continue
                raise  # re-raise non-429 errors immediately
        raise last_exc  # all keys exhausted

    llm_mod.LLMClient.chat = _rotating_chat
    print(
        f"[KeyRotator] Key rotation active — {len(keys)} Gemini keys loaded.",
        flush=True,
    )
else:
    print("[KeyRotator] Single key mode (add GEMINI_API_KEY_2 for rotation).", flush=True)

# ── Delegate to ApplyPilot's real CLI ────────────────────────────────────────
from applypilot.__main__ import app  # noqa: E402

app()

