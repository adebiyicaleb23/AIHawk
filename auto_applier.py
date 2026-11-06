#!/usr/bin/env python3
"""
ApplyPilot Gemini-Powered Auto-Applier
-------------------------------------
Takes tailored jobs from applypilot.db, launches Playwright browser,
uploads the matching tailored resume PDF, fills candidate details
(using MY_EMAIL, MY_EMAIL_PASSWORD, profile.json), uses Gemini to answer
screening questions, navigates multi-step forms, and submits applications automatically!
"""
import os
import sys
import json
import time
import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("AutoApplier")

APPLYPILOT_DIR = Path(os.environ.get("APPLYPILOT_DIR", Path.home() / ".applypilot"))
DB_PATH = APPLYPILOT_DIR / "applypilot.db"
PROFILE_PATH = APPLYPILOT_DIR / "profile.json"

if not DB_PATH.exists():
    local_db = Path("applypilot.db")
    if local_db.exists():
        DB_PATH = local_db

# Load candidate profile
profile = {}
for p_candidate in [PROFILE_PATH, Path("profile.json")]:
    if p_candidate.exists():
        try:
            with open(p_candidate, "r", encoding="utf-8") as f:
                profile = json.load(f)
                break
        except Exception as e:
            log.warning(f"Failed to read {p_candidate}: {e}")

personal = profile.get("personal", {})
candidate_email = os.environ.get("MY_EMAIL") or personal.get("email", "")
candidate_password = os.environ.get("MY_EMAIL_PASSWORD") or personal.get("password", "")
candidate_name = personal.get("full_name", "Iyanuoluwa Adebiyi")
candidate_first = personal.get("preferred_name") or candidate_name.split()[0]
candidate_last = candidate_name.split()[-1] if len(candidate_name.split()) > 1 else ""
candidate_phone = personal.get("phone", "+2347050301256")
candidate_city = personal.get("city", "Abuja")
candidate_country = personal.get("country", "Nigeria")
candidate_linkedin = personal.get("linkedin_url", "")
candidate_github = personal.get("github_url", "")
candidate_portfolio = personal.get("portfolio_url", "")

log.info(f"Auto-Applier initialized for: {candidate_name} ({candidate_email})")

# ── Gemini Assistant for Custom Form Questions ─────────────────────────────
keys = [
    os.environ.get("GEMINI_API_KEY", ""),
    os.environ.get("GEMINI_API_ACCESS", ""),
    os.environ.get("GEMINI_API_NAME", ""),
]
keys = [k.strip() for k in keys if k and len(k.strip()) > 15]

def ask_gemini(question_text: str) -> str:
    """Uses Gemini to answer job form screening questions."""
    import httpx
    prompt = f"""You are answering an application screening question for a candidate.
Candidate profile:
- Name: {candidate_name}
- Email: {candidate_email}
- Phone: {candidate_phone}
- Location: {candidate_city}, {candidate_country} (Seeking remote work, authorized for international remote contracts)
- Experience: 5 years in AI Evaluation, Data Annotation, RLHF, Virtual Assistance, Administration
- Education: Master's degree
- Notice period: Available immediately
- Willing to work remote: Yes

Question: {question_text}

Provide ONLY the direct, concise answer suitable for a form input (e.g. 'Yes', '5', 'Immediately', or a 1-sentence answer). Do not explain."""

    for key in keys:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            with httpx.Client(timeout=15) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    ans = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    return ans
        except Exception:
            continue
    return "Yes"

# ── Main Auto-Apply Engine ──────────────────────────────────────────────────
def run_auto_apply() -> dict:
    from playwright.sync_api import sync_playwright

    if not DB_PATH.exists():
        log.warning(f"Database not found at {DB_PATH}. Skipping auto-apply pass.")
        return {"applied": 0, "ready": 0, "total": 0}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Query jobs that have a tailored resume ready to submit
    cursor.execute("""
        SELECT url, title, site, application_url, tailored_resume_path, fit_score
        FROM jobs
        WHERE tailored_resume_path IS NOT NULL
          AND (apply_status IS NULL OR apply_status != 'applied')
        ORDER BY fit_score DESC
    """)
    eligible_jobs = cursor.fetchall()

    if not eligible_jobs:
        log.info("No unapplied tailored jobs pending.")
        conn.close()
        return {"applied": 0, "ready": 0, "total": 0}

    log.info(f"=== Starting Auto-Apply pass for {len(eligible_jobs)} tailored jobs ===")
    applied_count = 0
    ready_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )

        for job in eligible_jobs:
            job_url, title, site, app_url, resume_path_str, score = job
            target_url = app_url or job_url
            if not target_url.startswith("http"):
                log.info(f"Skipping invalid URL: {target_url} for '{title}'")
                continue

            # Locate the resume PDF file
            resume_file = Path(resume_path_str)
            if not resume_file.exists():
                for alt in [
                    APPLYPILOT_DIR / "tailored_resumes" / resume_file.name,
                    APPLYPILOT_DIR / resume_path_str,
                    Path("tailored_resumes") / resume_file.name,
                    APPLYPILOT_DIR / "resume.pdf",
                    Path("resume.pdf"),
                ]:
                    if alt.exists():
                        resume_file = alt
                        break

            log.info(f"\n---> Applying to: '{title}' [{site or 'Web'}]")
            log.info(f"     Target URL: {target_url}")

            page = context.new_page()
            try:
                page.goto(target_url, timeout=45000, wait_until="domcontentloaded")
                time.sleep(3)

                # 1. Click initial Apply / Easy Apply buttons
                apply_selectors = [
                    "button:has-text('Apply')",
                    "a:has-text('Apply')",
                    "button:has-text('Easy Apply')",
                    "a:has-text('Easy Apply')",
                    "[data-automation-id='applyButton']",
                    "button:has-text('Apply Now')",
                    "a:has-text('Apply Now')",
                    "a:has-text('Apply with Resume')",
                ]
                for sel in apply_selectors:
                    try:
                        btn = page.query_selector(sel)
                        if btn and btn.is_visible():
                            log.info(f"Clicked initial apply trigger: {sel}")
                            btn.click()
                            time.sleep(3)
                            break
                    except Exception:
                        pass

                # Multi-step progression loop (handles forms with Continue/Next/Submit)
                submitted = False
                for step_num in range(4):
                    # Fill standard email & password
                    email_inputs = page.query_selector_all("input[type='email'], input[name*='email' i], input[id*='email' i]")
                    for inp in email_inputs:
                        try:
                            if inp.is_visible() and not inp.input_value():
                                inp.fill(candidate_email)
                        except Exception:
                            pass

                    pwd_inputs = page.query_selector_all("input[type='password'], input[name*='password' i]")
                    for inp in pwd_inputs:
                        try:
                            if inp.is_visible() and not inp.input_value() and candidate_password:
                                inp.fill(candidate_password)
                        except Exception:
                            pass

                    # Fill Name fields
                    name_inputs = page.query_selector_all("input[name*='name' i], input[id*='name' i]")
                    for inp in name_inputs:
                        try:
                            if inp.is_visible() and not inp.input_value():
                                attr = ((inp.get_attribute("name") or "") + " " + (inp.get_attribute("id") or "")).lower()
                                if "first" in attr:
                                    inp.fill(candidate_first)
                                elif "last" in attr:
                                    inp.fill(candidate_last)
                                elif "full" in attr:
                                    inp.fill(candidate_name)
                        except Exception:
                            pass

                    # Fill Phone, Location, URLs
                    phone_inputs = page.query_selector_all("input[type='tel'], input[name*='phone' i], input[id*='phone' i]")
                    for inp in phone_inputs:
                        try:
                            if inp.is_visible() and not inp.input_value():
                                inp.fill(candidate_phone)
                        except Exception:
                            pass

                    # Links
                    url_inputs = page.query_selector_all("input[type='url'], input[name*='linkedin' i], input[name*='portfolio' i]")
                    for inp in url_inputs:
                        try:
                            if inp.is_visible() and not inp.input_value():
                                attr = ((inp.get_attribute("name") or "") + " " + (inp.get_attribute("id") or "")).lower()
                                if "linkedin" in attr and candidate_linkedin:
                                    inp.fill(candidate_linkedin)
                                elif candidate_portfolio:
                                    inp.fill(candidate_portfolio)
                        except Exception:
                            pass

                    # Upload Resume PDF
                    if resume_file.exists():
                        file_inputs = page.query_selector_all("input[type='file']")
                        for finp in file_inputs:
                            try:
                                finp.set_input_files(str(resume_file))
                                log.info(f"Uploaded tailored resume PDF: {resume_file.name}")
                                time.sleep(2)
                                break
                            except Exception:
                                pass

                    # Screening questions / textareas
                    unanswered = page.query_selector_all("textarea, input[type='text']:not([readonly])")
                    for inp in unanswered:
                        try:
                            if inp.is_visible() and not inp.input_value():
                                label_text = ""
                                inp_id = inp.get_attribute("id")
                                if inp_id:
                                    lbl = page.query_selector(f"label[for='{inp_id}']")
                                    if lbl:
                                        label_text = lbl.inner_text()
                                if not label_text:
                                    label_text = inp.get_attribute("placeholder") or inp.get_attribute("aria-label") or inp.get_attribute("name") or ""
                                if label_text and len(label_text.strip()) > 3:
                                    answer = ask_gemini(label_text)
                                    inp.fill(answer)
                        except Exception:
                            pass

                    # Affirmative checkboxes / radio buttons
                    radios = page.query_selector_all("input[type='radio'], input[type='checkbox']")
                    for r in radios:
                        try:
                            if not r.is_checked():
                                parent = r.evaluate_handle("el => el.closest('label') || el.parentElement")
                                txt = (parent.as_element().inner_text() if parent and parent.as_element() else "").lower()
                                if any(w in txt for w in ["yes", "agree", "i accept", "authorized", "eligible"]):
                                    r.check(force=True)
                        except Exception:
                            pass

                    # Check for Submit button first
                    submit_selectors = [
                        "button[type='submit']",
                        "button:has-text('Submit Application')",
                        "button:has-text('Submit')",
                        "[data-automation-id='submitButton']",
                    ]
                    for sel in submit_selectors:
                        try:
                            sbtn = page.query_selector(sel)
                            if sbtn and sbtn.is_visible():
                                sbtn.click()
                                log.info(f"Submitted application via {sel}!")
                                submitted = True
                                time.sleep(3)
                                break
                        except Exception:
                            pass

                    if submitted:
                        break

                    # Check for Next / Continue / Review buttons
                    next_selectors = [
                        "button:has-text('Continue')",
                        "button:has-text('Next')",
                        "button:has-text('Review')",
                        "a:has-text('Continue')",
                        "a:has-text('Next')",
                    ]
                    advanced = False
                    for nsel in next_selectors:
                        try:
                            nbtn = page.query_selector(nsel)
                            if nbtn and nbtn.is_visible():
                                log.info(f"Advancing multi-step application form: {nsel}")
                                nbtn.click()
                                advanced = True
                                time.sleep(3)
                                break
                        except Exception:
                            pass

                    if not advanced:
                        break

                # Record outcome
                status = "applied" if submitted else "ready_to_apply"
                cursor.execute(
                    "UPDATE jobs SET apply_status = ?, applied_at = ?, apply_attempts = apply_attempts + 1 WHERE url = ?",
                    (status, time.strftime("%Y-%m-%d %H:%M:%S") if submitted else None, job_url)
                )
                conn.commit()

                if submitted:
                    applied_count += 1
                    print(f"🎉 [SUCCESS] Applied to '{title}' at {site or 'company site'}!", flush=True)
                else:
                    ready_count += 1
                    print(f"ℹ️ [READY] Tailored & prepared for '{title}' (URL: {target_url})", flush=True)

            except Exception as e:
                log.warning(f"Error processing '{title}': {e}")
                cursor.execute("UPDATE jobs SET apply_status = 'error', apply_error = ? WHERE url = ?", (str(e)[:200], job_url))
                conn.commit()
            finally:
                page.close()

        browser.close()

    conn.close()
    log.info(f"Auto-apply pass finished: {applied_count} submitted, {ready_count} prepared.")
    return {"applied": applied_count, "ready": ready_count, "total": len(eligible_jobs)}

if __name__ == "__main__":
    run_auto_apply()
