#!/usr/bin/env python3
"""
ApplyPilot Bootstrap Database & Assets Loader
--------------------------------------------
Seeds applypilot.db with verified high-scoring tailored jobs and matching
resume PDFs so the auto-applier can submit applications immediately!
"""
import os
import json
import sqlite3
import shutil
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("BootstrapDB")

APPLYPILOT_DIR = Path(os.environ.get("APPLYPILOT_DIR", Path.home() / ".applypilot"))
DB_PATH = APPLYPILOT_DIR / "applypilot.db"
SEED_FILE = Path("seed_jobs.json")
ASSETS_DIR = Path("assets/resumes")
TAILORED_DIR = APPLYPILOT_DIR / "tailored_resumes"

def bootstrap():
    APPLYPILOT_DIR.mkdir(parents=True, exist_ok=True)
    TAILORED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Copy pre-generated tailored PDFs into runner storage
    if ASSETS_DIR.exists():
        for pdf_file in ASSETS_DIR.glob("*.pdf"):
            shutil.copy(pdf_file, TAILORED_DIR / pdf_file.name)
            log.info(f"Loaded tailored PDF: {pdf_file.name}")

    # 2. Initialize database schema
    from applypilot.database import init_db
    conn = init_db(DB_PATH)
    cursor = conn.cursor()

    # 3. Seed verified jobs
    if SEED_FILE.exists():
        with open(SEED_FILE, "r", encoding="utf-8") as f:
            jobs = json.load(f)

        loaded_count = 0
        for job in jobs:
            url = job.get("url")
            # Update path to runner location
            orig_path = Path(job.get("tailored_resume_path", ""))
            runner_resume_path = str(TAILORED_DIR / orig_path.name)

            cursor.execute("""
                INSERT INTO jobs (
                    url, title, salary, description, location, site, strategy, discovered_at,
                    full_description, application_url, detail_scraped_at, detail_error,
                    fit_score, score_reasoning, scored_at,
                    tailored_resume_path, tailored_at, tailor_attempts,
                    cover_letter_path, cover_letter_at, cover_attempts,
                    apply_status, apply_attempts
                ) VALUES (
                    :url, :title, :salary, :description, :location, :site, :strategy, :discovered_at,
                    :full_description, :application_url, :detail_scraped_at, :detail_error,
                    :fit_score, :score_reasoning, :scored_at,
                    :tailored_resume_path, :tailored_at, :tailor_attempts,
                    :cover_letter_path, :cover_letter_at, :cover_attempts,
                    NULL, 0
                )
                ON CONFLICT(url) DO UPDATE SET
                    tailored_resume_path = excluded.tailored_resume_path,
                    fit_score = excluded.fit_score
            """, {
                "url": url,
                "title": job.get("title"),
                "salary": job.get("salary"),
                "description": job.get("description"),
                "location": job.get("location"),
                "site": job.get("site"),
                "strategy": job.get("strategy"),
                "discovered_at": job.get("discovered_at"),
                "full_description": job.get("full_description"),
                "application_url": job.get("application_url"),
                "detail_scraped_at": job.get("detail_scraped_at"),
                "detail_error": job.get("detail_error"),
                "fit_score": job.get("fit_score"),
                "score_reasoning": job.get("score_reasoning"),
                "scored_at": job.get("scored_at"),
                "tailored_resume_path": runner_resume_path,
                "tailored_at": job.get("tailored_at"),
                "tailor_attempts": job.get("tailor_attempts", 1),
                "cover_letter_path": job.get("cover_letter_path"),
                "cover_letter_at": job.get("cover_letter_at"),
                "cover_attempts": job.get("cover_attempts", 1),
            })
            loaded_count += 1

        conn.commit()
        log.info(f"Successfully seeded {loaded_count} pre-tailored high-fit jobs into {DB_PATH}")

    conn.close()

if __name__ == "__main__":
    bootstrap()
