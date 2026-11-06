#!/usr/bin/env python3
"""
ApplyPilot End-to-End Query-by-Query Loop Orchestrator
-----------------------------------------------------
Processes job search queries one by one in priority order:
1. ALL AI Jobs FIRST (Tier 1: AI Trainer, AI Data Evaluator, RLHF, etc.)
2. Administrative & Client Support (Tier 2: Virtual Assistant, Customer Support, etc.)
3. Freelance & Creative Roles LAST (Tier 3: Social Media, Graphic Design, Video Editing)

For each query:
- Discovers jobs from job boards (5 results/site)
- Enriches job descriptions
- Scores jobs against candidate profile with Gemini (3-key auto-rotation)
- Generates tailored resume PDF and cover letter
- Auto-applies immediately with Playwright browser + Gemini screening question answering
- Advances to the next query!
"""
import os
import sys
import yaml
import time
import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("Orchestrator")

APPLYPILOT_DIR = Path(os.environ.get("APPLYPILOT_DIR", Path.home() / ".applypilot"))
MASTER_SEARCHES_PATH = Path("searches.yaml")
RUNNER_SEARCHES_PATH = APPLYPILOT_DIR / "searches.yaml"
DB_PATH = APPLYPILOT_DIR / "applypilot.db"

if not DB_PATH.exists():
    local_db = Path("applypilot.db")
    if local_db.exists():
        DB_PATH = local_db

# ── 1. Activate 3-Key Instant Gemini Rotation ───────────────────────────────
import applypilot.llm as llm_mod

candidate_vars = ["GEMINI_API_KEY", "GEMINI_API_ACCESS", "GEMINI_API_NAME"]
keys = []
for var in candidate_vars:
    val = os.environ.get(var, "").strip()
    if val and val not in keys and len(val) > 15:
        keys.append(val)

for k, v in sorted(os.environ.items()):
    val = v.strip()
    if k.startswith("GEMINI_") and val and val not in keys and len(val) > 20:
        keys.append(val)

if keys:
    key_index = 0
    _orig_chat_compat = llm_mod.LLMClient._chat_compat

    def _rotate_key(self):
        global key_index
        key_index = (key_index + 1) % len(keys)
        self.api_key = keys[key_index]
        log.info(f"[KeyRotator] Rate limit hit! Instantly rotated to Gemini key #{key_index + 1}")

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
        return _orig_chat_compat(self, messages, temperature, max_tokens)

    llm_mod.LLMClient._chat_compat = _fast_chat_compat
    log.info(f"[KeyRotator] Instant rotation active across {len(keys)} Gemini keys.")
else:
    log.warning("[KeyRotator] No Gemini keys found in environment.")

# ── 2. Load Master Search Queries ───────────────────────────────────────────
if not MASTER_SEARCHES_PATH.exists():
    log.error(f"Master searches file not found: {MASTER_SEARCHES_PATH}")
    sys.exit(1)

with open(MASTER_SEARCHES_PATH, "r", encoding="utf-8") as f:
    master_cfg = yaml.safe_load(f)

queries = master_cfg.get("queries", [])
if not queries:
    log.error("No queries found in searches.yaml!")
    sys.exit(1)

log.info(f"Loaded {len(queries)} job categories to execute sequentially in priority order.")

# ── 3. Query-by-Query Execution Loop ────────────────────────────────────────
from applypilot import pipeline
from auto_applier import run_auto_apply

total_queries = len(queries)
for idx, q_item in enumerate(queries, 1):
    query_text = q_item.get("query", "")
    tier = q_item.get("tier", 1)
    
    print("\n" + "=" * 80, flush=True)
    print(f"🚀 [STEP {idx}/{total_queries}] CATEGORY: '{query_text}' (Tier {tier})", flush=True)
    print("=" * 80, flush=True)

    # Prepare single-query config for ApplyPilot
    # Use LinkedIn + ZipRecruiter only: Indeed blocks GitHub Actions cloud IPs (403/429)
    # Use hours_old=168 (7 days) so fresh-but-not-brand-new AI postings are captured
    single_cfg = {
        "defaults": {
            "location": "Remote",
            "distance": 0,
            "hours_old": 168,
            "results_per_site": 10,
        },
        "sites": ["linkedin", "zip_recruiter"],
        "locations": [
            {"location": "Remote", "remote": True}
        ],
        "queries": [
            {"query": query_text, "tier": 1}
        ]
    }

    # Write to runner searches.yaml
    RUNNER_SEARCHES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RUNNER_SEARCHES_PATH, "w", encoding="utf-8") as f:
        yaml.dump(single_cfg, f, default_flow_style=False)

    # Also sync local searches.yaml if running locally
    if RUNNER_SEARCHES_PATH != MASTER_SEARCHES_PATH:
        try:
            with open("searches.yaml", "w", encoding="utf-8") as f:
                yaml.dump(single_cfg, f, default_flow_style=False)
        except Exception:
            pass

    # Step A: Run ApplyPilot Discovery, Enrichment, Scoring & Tailoring
    try:
        log.info(f"Running pipeline for '{query_text}'...")
        pipeline.run_pipeline(
            stages=["discover", "enrich", "score", "tailor", "cover", "pdf"],
            min_score=7,
            validation_mode="lenient"
        )
    except Exception as e:
        log.warning(f"Pipeline notice for '{query_text}': {e}")

    # Step B: Auto-Apply immediately to all tailored jobs from this category!
    try:
        log.info(f"Running auto-applier for '{query_text}'...")
        apply_stats = run_auto_apply()
        print(f"✅ [PROGRESS] '{query_text}' completed: {apply_stats.get('applied', 0)} submitted, {apply_stats.get('ready', 0)} prepared.", flush=True)
    except Exception as e:
        log.error(f"Auto-applier error for '{query_text}': {e}")

    time.sleep(2)

# Restore master searches.yaml
with open(MASTER_SEARCHES_PATH, "w", encoding="utf-8") as f:
    yaml.dump(master_cfg, f, default_flow_style=False)
with open(RUNNER_SEARCHES_PATH, "w", encoding="utf-8") as f:
    yaml.dump(master_cfg, f, default_flow_style=False)

# ── 4. Final DB Summary ─────────────────────────────────────────────────────
print("\n" + "=" * 80, flush=True)
print("🎉 ALL 15 JOB CATEGORIES COMPLETED!", flush=True)
print("=" * 80, flush=True)

if DB_PATH.exists():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT count(*) FROM jobs")
        total_jobs = c.fetchone()[0]
        c.execute("SELECT count(*) FROM jobs WHERE tailored_resume_path IS NOT NULL")
        tailored_jobs = c.fetchone()[0]
        c.execute("SELECT count(*) FROM jobs WHERE apply_status = 'applied'")
        applied_jobs = c.fetchone()[0]
        c.execute("SELECT count(*) FROM jobs WHERE apply_status = 'ready_to_apply'")
        ready_jobs = c.fetchone()[0]

        print(f"  Total Jobs Found:     {total_jobs}")
        print(f"  Tailored Resumes:     {tailored_jobs}")
        print(f"  Applications Applied: {applied_jobs}")
        print(f"  Ready for Review:     {ready_jobs}")
        print("=" * 80 + "\n", flush=True)
        conn.close()
    except Exception as e:
        log.warning(f"Could not print final summary: {e}")

