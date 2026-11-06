#!/usr/bin/env python3
"""
ApplyPilot Gemini-Powered Auto-Applier
--------------------------------------
Automatically creates accounts and applies to jobs on ANY portal:
- Workday (myworkdayjobs.com)
- Greenhouse (boards.greenhouse.io)
- Lever (jobs.lever.co)
- LinkedIn Easy Apply
- Generic portals with signup forms

Credentials used:
  MY_EMAIL          -> candidate's email (from GitHub Secrets)
  MY_EMAIL_PASSWORD -> candidate's password (from GitHub Secrets)
  DOB               -> 23/12/2004 (stored in profile.json)
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
candidate_email    = os.environ.get("MY_EMAIL") or personal.get("email", "adebiyicaleb222@gmail.com")
candidate_password = os.environ.get("MY_EMAIL_PASSWORD") or personal.get("password", "")
candidate_name     = personal.get("full_name", "Iyanuoluwa Adebiyi")
candidate_first    = personal.get("preferred_name") or candidate_name.split()[0]
candidate_last     = candidate_name.split()[-1] if len(candidate_name.split()) > 1 else ""
candidate_phone    = personal.get("phone", "+2347050301256")
candidate_city     = personal.get("city", "Abuja")
candidate_country  = personal.get("country", "Nigeria")
candidate_linkedin = personal.get("linkedin_url", "")
candidate_portfolio= personal.get("portfolio_url", "")
candidate_dob_day  = personal.get("dob_day", "23")
candidate_dob_month= personal.get("dob_month", "12")
candidate_dob_year = personal.get("dob_year", "2004")
candidate_dob      = personal.get("dob", "23/12/2004")

log.info(f"Auto-Applier ready for: {candidate_name} ({candidate_email})")

# ── Gemini Answer Engine ────────────────────────────────────────────────────
keys = [k.strip() for k in [
    os.environ.get("GEMINI_API_KEY", ""),
    os.environ.get("GEMINI_API_ACCESS", ""),
    os.environ.get("GEMINI_API_NAME", ""),
] if k and len(k.strip()) > 15]

def ask_gemini(question_text: str) -> str:
    import httpx
    prompt = f"""You are answering a job application screening question for this candidate:
- Name: {candidate_name}
- Email: {candidate_email}
- Phone: {candidate_phone}
- Location: {candidate_city}, {candidate_country} (Remote work, authorized for international remote contracts)
- Experience: 5 years — AI Evaluation, Data Annotation, RLHF, Virtual Assistance, Administration
- Education: Master's degree
- DOB: {candidate_dob}
- Notice period: Available immediately
- Remote: Yes

Question: {question_text}

Reply with ONLY the direct concise answer for a form field (e.g. 'Yes', '5', 'Immediately', a 1-sentence answer, or a number). No explanation."""
    for key in keys:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={key}"
            with httpx.Client(timeout=15) as c:
                resp = c.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
                if resp.status_code == 200:
                    return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            continue
    return "Yes"

# ── Portal Account Creation Helpers ────────────────────────────────────────

def _fill_field(page, selectors: list, value: str, label: str = ""):
    """Try a list of CSS selectors and fill the first visible empty one."""
    for sel in selectors:
        try:
            els = page.query_selector_all(sel)
            for el in els:
                if el.is_visible() and not el.input_value():
                    el.fill(value)
                    log.info(f"  Filled {label or sel}")
                    return True
        except Exception:
            pass
    return False

def _click_first(page, selectors: list, label: str = "") -> bool:
    """Click the first visible matching element."""
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.click()
                log.info(f"  Clicked: {label or sel}")
                time.sleep(2)
                return True
        except Exception:
            pass
    return False

def handle_workday_auth(page) -> bool:
    """
    Detect Workday sign-in page and either login or create account.
    Returns True if auth was handled successfully.
    """
    url = page.url
    if "myworkdayjobs.com" not in url and "workday.com" not in url:
        # check for Workday sign-in elements
        signin_elem = page.query_selector("[data-automation-id='signInSection'], [data-automation-id='createAccountLink']")
        if not signin_elem:
            return False

    log.info("Workday auth detected — attempting login/signup...")

    # Try to sign in first
    email_sel = "[data-automation-id='email'], input[name='username'], input[type='email']"
    pwd_sel = "[data-automation-id='password'], input[type='password']"

    email_inp = page.query_selector(email_sel)
    if email_inp and email_inp.is_visible():
        email_inp.fill(candidate_email)
        time.sleep(0.5)
        pwd_inp = page.query_selector(pwd_sel)
        if pwd_inp and pwd_inp.is_visible():
            pwd_inp.fill(candidate_password)
            time.sleep(0.5)
            # Click Sign In
            if _click_first(page, [
                "[data-automation-id='signInSubmitButton']",
                "button:has-text('Sign In')",
                "button[type='submit']",
            ], "Sign In button"):
                time.sleep(4)
                # Check if still on sign-in page (login may have failed)
                still_signin = page.query_selector("[data-automation-id='signInSection']")
                if not still_signin:
                    log.info("Workday: Signed in successfully!")
                    return True
                log.info("Workday: Sign-in failed (no account?). Trying Create Account...")

    # Click "Create Account" link
    if _click_first(page, [
        "[data-automation-id='createAccountLink']",
        "a:has-text('Create Account')",
        "button:has-text('Create Account')",
        "a:has-text('Sign Up')",
    ], "Create Account"):
        time.sleep(3)
        # Fill registration form
        _fill_field(page, ["[data-automation-id='email'], input[name='email'], input[type='email']"], candidate_email, "email")
        _fill_field(page, ["[data-automation-id='password'], input[type='password'][name*='pass' i]"], candidate_password, "password")
        _fill_field(page, ["[data-automation-id='verifyPassword'], input[id*='confirm' i], input[name*='confirm' i]"], candidate_password, "confirm password")
        _fill_field(page, ["input[name*='firstName' i], input[id*='firstName' i]"], candidate_first, "first name")
        _fill_field(page, ["input[name*='lastName' i], input[id*='lastName' i]"], candidate_last, "last name")

        # Click Create Account submit
        if _click_first(page, [
            "[data-automation-id='createAccountSubmitButton']",
            "button:has-text('Create Account')",
            "button[type='submit']",
        ], "Create Account submit"):
            time.sleep(5)
            log.info("Workday: Account creation submitted!")
            return True

    return False

def handle_greenhouse_auth(page) -> bool:
    """Handle Greenhouse job board application (no account required usually)."""
    if "greenhouse.io" not in page.url and "greenhouse.io" not in page.content()[:500]:
        return False
    log.info("Greenhouse portal detected — filling direct application form...")
    return True  # Greenhouse forms are usually direct, handled by main fill logic

def handle_lever_auth(page) -> bool:
    """Handle Lever job board application (no account required usually)."""
    if "lever.co" not in page.url:
        return False
    log.info("Lever portal detected — filling direct application form...")
    return True  # Lever forms are usually direct

def handle_generic_signup(page) -> bool:
    """
    Generic account creation for any portal showing a signup/registration form.
    Triggered when standard form fields like 'Create Account', 'Register', 'Sign Up' appear.
    """
    # Detect signup indicators
    signup_indicators = [
        "button:has-text('Create Account')",
        "button:has-text('Register')",
        "button:has-text('Sign Up')",
        "a:has-text('Create Account')",
        "a:has-text('Sign Up')",
        "h1:has-text('Create Account')",
        "h2:has-text('Register')",
    ]
    found = False
    for sel in signup_indicators:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                found = True
                break
        except Exception:
            pass
    if not found:
        return False

    log.info("Generic signup form detected — attempting auto-registration...")

    # Try to sign in first with existing credentials
    _fill_field(page, ["input[type='email'], input[name*='email' i], input[id*='email' i]"], candidate_email, "email (login attempt)")
    _fill_field(page, ["input[type='password']"], candidate_password, "password (login attempt)")

    login_clicked = _click_first(page, [
        "button:has-text('Sign In')",
        "button:has-text('Log In')",
        "button:has-text('Login')",
        "button[type='submit']",
    ], "Login button")

    if login_clicked:
        time.sleep(4)
        # Check if signup form is gone (success)
        still_signup = any(page.query_selector(s) for s in signup_indicators[:3] if page.query_selector(s))
        if not still_signup:
            log.info("Generic portal: Logged in successfully!")
            return True

    # Try Create Account flow
    _click_first(page, [
        "button:has-text('Create Account')",
        "a:has-text('Create Account')",
        "button:has-text('Register')",
        "a:has-text('Sign Up')",
    ], "Create Account link")
    time.sleep(2)

    # Fill all standard registration fields
    _fill_field(page, ["input[name*='firstName' i], input[id*='firstName' i], input[placeholder*='First' i]"], candidate_first, "first name")
    _fill_field(page, ["input[name*='lastName' i], input[id*='lastName' i], input[placeholder*='Last' i]"], candidate_last, "last name")
    _fill_field(page, ["input[type='email'], input[name*='email' i]"], candidate_email, "email")
    _fill_field(page, ["input[type='password']"], candidate_password, "password")
    _fill_field(page, ["input[name*='confirm' i], input[id*='confirm' i]"], candidate_password, "confirm password")
    _fill_field(page, ["input[type='tel'], input[name*='phone' i]"], candidate_phone, "phone")

    # DOB fields
    _fill_field(page, ["input[name*='dob' i], input[name*='birthdate' i], input[name*='birthday' i]"], candidate_dob, "DOB")
    _fill_field(page, ["input[name*='birth_day' i], input[id*='day' i][name*='day' i]"], candidate_dob_day, "DOB day")
    _fill_field(page, ["input[name*='birth_month' i], input[id*='month' i]"], candidate_dob_month, "DOB month")
    _fill_field(page, ["input[name*='birth_year' i], input[id*='year' i]"], candidate_dob_year, "DOB year")

    _click_first(page, [
        "button[type='submit']",
        "button:has-text('Create Account')",
        "button:has-text('Register')",
        "button:has-text('Sign Up')",
    ], "Register submit")
    time.sleep(5)
    return True

# ── Full Application Form Filler ───────────────────────────────────────────

def fill_application_form(page, resume_file: Path):
    """Fill all standard application form fields and upload resume."""
    # Email
    for inp in page.query_selector_all("input[type='email'], input[name*='email' i], input[id*='email' i]"):
        try:
            if inp.is_visible() and not inp.input_value():
                inp.fill(candidate_email)
        except Exception:
            pass

    # Password (if re-asked after account creation)
    for inp in page.query_selector_all("input[type='password']"):
        try:
            if inp.is_visible() and not inp.input_value():
                inp.fill(candidate_password)
        except Exception:
            pass

    # Name fields
    for inp in page.query_selector_all("input[name*='name' i], input[id*='name' i], input[placeholder*='name' i]"):
        try:
            if inp.is_visible() and not inp.input_value():
                attr = ((inp.get_attribute("name") or "") + " " + (inp.get_attribute("id") or "") + " " + (inp.get_attribute("placeholder") or "")).lower()
                if "first" in attr:
                    inp.fill(candidate_first)
                elif "last" in attr:
                    inp.fill(candidate_last)
                elif "full" in attr or "name" in attr:
                    inp.fill(candidate_name)
        except Exception:
            pass

    # Phone
    for inp in page.query_selector_all("input[type='tel'], input[name*='phone' i], input[id*='phone' i]"):
        try:
            if inp.is_visible() and not inp.input_value():
                inp.fill(candidate_phone)
        except Exception:
            pass

    # Location / City / Country
    for inp in page.query_selector_all("input[name*='city' i], input[id*='city' i], input[placeholder*='city' i]"):
        try:
            if inp.is_visible() and not inp.input_value():
                inp.fill(candidate_city)
        except Exception:
            pass

    for inp in page.query_selector_all("input[name*='country' i], input[id*='country' i]"):
        try:
            if inp.is_visible() and not inp.input_value():
                inp.fill(candidate_country)
        except Exception:
            pass

    # LinkedIn / Portfolio URLs
    for inp in page.query_selector_all("input[type='url'], input[name*='linkedin' i], input[id*='linkedin' i]"):
        try:
            if inp.is_visible() and not inp.input_value() and candidate_linkedin:
                inp.fill(candidate_linkedin)
        except Exception:
            pass

    for inp in page.query_selector_all("input[name*='portfolio' i], input[name*='website' i], input[name*='github' i]"):
        try:
            if inp.is_visible() and not inp.input_value() and candidate_portfolio:
                inp.fill(candidate_portfolio)
        except Exception:
            pass

    # DOB fields
    for inp in page.query_selector_all("input[name*='dob' i], input[name*='birthdate' i], input[name*='birthday' i]"):
        try:
            if inp.is_visible() and not inp.input_value():
                inp.fill(candidate_dob)
        except Exception:
            pass

    # Resume upload
    if resume_file.exists():
        for finp in page.query_selector_all("input[type='file']"):
            try:
                finp.set_input_files(str(resume_file))
                log.info(f"  Uploaded resume: {resume_file.name}")
                time.sleep(2)
                break
            except Exception:
                pass

    # Screening questions / textareas
    for inp in page.query_selector_all("textarea, input[type='text']:not([readonly])"):
        try:
            if not inp.is_visible() or inp.input_value():
                continue
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

    # Affirmative checkboxes
    for r in page.query_selector_all("input[type='radio'], input[type='checkbox']"):
        try:
            if not r.is_checked():
                parent = r.evaluate_handle("el => el.closest('label') || el.parentElement")
                txt = (parent.as_element().inner_text() if parent and parent.as_element() else "").lower()
                if any(w in txt for w in ["yes", "agree", "accept", "authorized", "eligible", "confirm"]):
                    r.check(force=True)
        except Exception:
            pass


# ── Main Auto-Apply Engine ─────────────────────────────────────────────────
def run_auto_apply() -> dict:
    from playwright.sync_api import sync_playwright

    if not DB_PATH.exists():
        log.warning(f"Database not found at {DB_PATH}. Skipping auto-apply.")
        return {"applied": 0, "ready": 0, "total": 0}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT url, title, site, application_url, tailored_resume_path, fit_score
        FROM jobs
        WHERE tailored_resume_path IS NOT NULL
          AND (apply_status IS NULL OR apply_status NOT IN ('applied', 'portal_gated'))
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
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )

        for job in eligible_jobs:
            job_url, title, site, app_url, resume_path_str, score = job
            target_url = app_url or job_url or ""

            if not target_url:
                log.info(f"Skipping '{title}' — no URL found.")
                continue

            # Normalize URL if scheme is missing
            if target_url.startswith("//"):
                target_url = "https:" + target_url
            elif target_url.startswith("www."):
                target_url = "https://" + target_url
            elif target_url.startswith("/") and site:
                site_domain = "talent.com" if "talent" in site.lower() else f"{site.lower().replace(' ', '')}.com"
                target_url = f"https://{site_domain}" + target_url
            elif not target_url.startswith("http://") and not target_url.startswith("https://"):
                target_url = "https://" + target_url

            log.info(f"\n---> [{score}/10] '{title}' at {site or 'Web'}")
            log.info(f"     URL: {target_url}")

            # Locate resume PDF (prioritize .pdf over .txt)
            raw_path = Path(resume_path_str)
            pdf_alt = raw_path.with_suffix('.pdf')
            resume_file = None
            for candidate in [
                pdf_alt,
                APPLYPILOT_DIR / "tailored_resumes" / pdf_alt.name,
                Path("tailored_resumes") / pdf_alt.name,
                Path("tailored_resumes") / "tailored_resumes" / pdf_alt.name,
                raw_path,
                APPLYPILOT_DIR / "tailored_resumes" / raw_path.name,
                Path("tailored_resumes") / raw_path.name,
                APPLYPILOT_DIR / "resume.pdf",
                Path("resume.pdf"),
            ]:
                if candidate.exists():
                    resume_file = candidate
                    break

            if not resume_file:
                resume_file = pdf_alt
            log.info(f"     Resume attachment: {resume_file.name}")

            page = context.new_page()
            try:
                page.goto(target_url, timeout=50000, wait_until="domcontentloaded")
                time.sleep(3)

                # ── Step 1: Click initial Apply button ────────────────────
                _click_first(page, [
                    "button:has-text('Apply')",
                    "a:has-text('Apply')",
                    "button:has-text('Easy Apply')",
                    "a:has-text('Easy Apply')",
                    "[data-automation-id='applyButton']",
                    "button:has-text('Apply Now')",
                    "a:has-text('Apply Now')",
                    "a:has-text('Apply with Resume')",
                ], "Apply button")

                # ── Step 2: Handle portal authentication / account creation ──
                # Workday
                if "myworkdayjobs.com" in page.url or "workday.com" in page.url:
                    handle_workday_auth(page)
                    time.sleep(3)
                # Greenhouse (usually no auth needed)
                elif "greenhouse.io" in page.url:
                    handle_greenhouse_auth(page)
                # Lever (usually no auth needed)
                elif "lever.co" in page.url:
                    handle_lever_auth(page)
                else:
                    # Generic: check for any signup/login wall
                    handle_generic_signup(page)
                    time.sleep(2)

                # ── Step 3: Multi-step form progression (up to 6 steps) ──
                submitted = False
                for step_num in range(6):
                    fill_application_form(page, resume_file)

                    # Try Submit
                    if _click_first(page, [
                        "button[type='submit']",
                        "button:has-text('Submit Application')",
                        "button:has-text('Submit')",
                        "[data-automation-id='submitButton']",
                        "button:has-text('Send Application')",
                    ], f"Submit (step {step_num+1})"):
                        submitted = True
                        time.sleep(3)
                        break

                    # Try Next / Continue
                    advanced = _click_first(page, [
                        "button:has-text('Continue')",
                        "button:has-text('Next')",
                        "button:has-text('Review')",
                        "a:has-text('Continue')",
                        "a:has-text('Next')",
                        "[data-automation-id='bottom-navigation-next-button']",
                    ], f"Continue/Next (step {step_num+1})")

                    if not advanced:
                        break

                # ── Step 4: Record outcome ───────────────────────────────
                status = "applied" if submitted else "ready_to_apply"
                cursor.execute(
                    "UPDATE jobs SET apply_status=?, applied_at=?, apply_attempts=apply_attempts+1 WHERE url=?",
                    (status, time.strftime("%Y-%m-%d %H:%M:%S") if submitted else None, job_url)
                )
                conn.commit()

                if submitted:
                    applied_count += 1
                    print(f"🎉 [SUCCESS] Applied to '{title}' at {site or 'company site'}!", flush=True)
                else:
                    ready_count += 1
                    print(f"ℹ️  [READY] Tailored & prepared: '{title}' | {target_url}", flush=True)

            except Exception as e:
                log.warning(f"Error on '{title}': {e}")
                cursor.execute("UPDATE jobs SET apply_status='error', apply_error=? WHERE url=?", (str(e)[:200], job_url))
                conn.commit()
            finally:
                page.close()

        browser.close()

    conn.close()
    log.info(f"Auto-apply pass complete: {applied_count} submitted, {ready_count} prepared.")
    return {"applied": applied_count, "ready": ready_count, "total": len(eligible_jobs)}


if __name__ == "__main__":
    run_auto_apply()
