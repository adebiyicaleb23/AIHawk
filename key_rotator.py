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

# ── Patch LLMClient to instantly rotate on 429 ──────────────────────────────
if len(keys) > 1:
    key_index = 0

    _orig_chat_compat = llm_mod.LLMClient._chat_compat
    _orig_chat_native = llm_mod.LLMClient._chat_native_gemini

    def _rotate_key(self):
        global key_index
        key_index = (key_index + 1) % len(keys)
        self.api_key = keys[key_index]
        print(f"[KeyRotator] Rate limit hit! Instantly switched to key #{key_index + 1}", flush=True)

    def _fast_chat_compat(self, messages, temperature, max_tokens):
        for _ in range(len(keys)):
            self.api_key = keys[key_index]
            resp = self._client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            )
            if resp.status_code == 429:
                _rotate_key(self)
                continue
            if resp.status_code == 403 and self._is_gemini:
                raise llm_mod._GeminiCompatForbidden(resp)
            return self._handle_compat_response(resp)
        # All keys hit 429 in a row; fall back to normal response so backoff can run
        return _orig_chat_compat(self, messages, temperature, max_tokens)

    llm_mod.LLMClient._chat_compat = _fast_chat_compat
    print(
        f"[KeyRotator] Instant rotation active across {len(keys)} Gemini keys.",
        flush=True,
    )
else:
    print("[KeyRotator] Single key mode (add GEMINI_API_KEY_2 for rotation).", flush=True)

# ── Delegate to ApplyPilot's real CLI ────────────────────────────────────────
from applypilot.__main__ import app  # noqa: E402

app()

