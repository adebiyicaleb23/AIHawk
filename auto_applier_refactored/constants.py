"""
ApplyPilot Constants

All magic numbers, timeouts, delays, and selectors centralized here.
NO hardcoded values should appear in other modules.
"""

from pathlib import Path

# ============================================================================
# Browser Configuration
# ============================================================================
BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# ============================================================================
# Timeouts (milliseconds)
# ============================================================================
PAGE_LOAD_TIMEOUT = 50_000
NAVIGATION_TIMEOUT = 30_000
FORM_WAIT_TIMEOUT = 10_000
ELEMENT_CLICK_TIMEOUT = 10_000
IFRAME_LOAD_TIMEOUT = 10_000
MODAL_WAIT_TIMEOUT = 10_000

# ============================================================================
# Delays (seconds)
# ============================================================================
POST_CLICK_DELAY = 2
POST_NAVIGATION_DELAY = 3
AUTH_FORM_DELAY = 5
STEP_TRANSITION_DELAY = 3
RESUME_UPLOAD_DELAY = 2
INITIAL_PAGE_LOAD_DELAY = 3
POST_APPLY_CLICK_DELAY = 5
LOGIN_CLICK_DELAY = 3
MODAL_OPEN_DELAY = 2

# ============================================================================
# Step Limits
# ============================================================================
WORKDAY_MAX_STEPS = 8
DEFAULT_MAX_STEPS = 6
MAX_AUTH_RETRY_ATTEMPTS = 5

# ============================================================================
# Database
# ============================================================================
DB_FILE_NAME = "applypilot.db"
PROFILE_FILE_NAME = "profile.json"
TAILORED_RESUMES_DIR = "tailored_resumes"

# ============================================================================
# Portal Domains
# ============================================================================
WORKDAY_DOMAINS = ("myworkdayjobs.com", "workday.com")
GREENHOUSE_DOMAIN = "greenhouse.io"
LEVER_DOMAIN = "lever.co"
LINKEDIN_DOMAIN = "linkedin.com"

# ============================================================================
# Selectors by Portal
# ============================================================================

# Workday Selectors
WORKDAY_SELECTORS = {
    "apply_button": [
        "button:has-text('Apply')",
        "a:has-text('Apply')",
        "[data-automation-id='applyButton']",
        "button:has-text('Apply Now')",
        "a:has-text('Apply Now')",
        "a:has-text('Apply with Resume')",
    ],
    "sign_in_link": [
        "button:has-text('Sign In')",
        "a:has-text('Sign In')",
        "[data-automation-id='signInLink']",
        "button:has-text('Log In')",
        "a:has-text('Log In')",
    ],
    "sign_in_with_email": [
        "button:has-text('Sign in with email')",
        "button:has-text('Continue with email')",
        "button:has-text('Use email')",
        "a:has-text('Sign in with email')",
        "a:has-text('Continue with email')",
        "[data-automation-id*='email' i]",
        "button[data-automation-id='emailLogin']",
    ],
    "create_account_link": [
        "[data-automation-id='createAccountLink']",
        "a:has-text('Create Account')",
        "button:has-text('Create Account')",
        "a:has-text('Sign Up')",
    ],
    "email_field": [
        "[data-automation-id='email']",
        "input[name='username']",
        "input[type='email']",
        "input[name*='email' i]",
    ],
    "password_field": [
        "[data-automation-id='password']",
        "input[type='password']",
    ],
    "sign_in_submit": [
        "[data-automation-id='signInSubmitButton']",
        "button:has-text('Sign In')",
        "button[type='submit']",
    ],
    "create_account_submit": [
        "[data-automation-id='createAccountSubmitButton']",
        "button:has-text('Create Account')",
        "button[type='submit']",
    ],
    "apply_form_indicators": [
        "[data-automation-id='applyForm']",
        "form[data-automation-id='jobApplicationForm']",
        "input[data-automation-id='firstName']",
        "input[data-automation-id='lastName']",
        "input[name*='firstName' i]",
        "input[name*='lastName' i]",
    ],
    "submit_button": [
        "[data-automation-id='submitButton']",
        "button[data-automation-id='submitButton']",
        "button:has-text('Submit Application')",
        "button:has-text('Submit')",
        "button[type='submit']",
        "button:has-text('Send Application')",
        "button:has-text('Apply Now')",
    ],
    "next_continue_button": [
        "[data-automation-id='bottom-navigation-next-button']",
        "[data-automation-id='navigationNextButton']",
        "[data-automation-id='nextButton']",
        "button[data-automation-id*='next' i]",
        "button[data-automation-id*='continue' i]",
        "button[data-automation-id*='review' i]",
        "button:has-text('Continue')",
        "button:has-text('Next')",
        "button:has-text('Review')",
        "button:has-text('Next: Review')",
        "button:has-text('Continue to Review')",
        "button:has-text('Submit Application')",
        "a:has-text('Continue')",
        "a:has-text('Next')",
        "a:has-text('Review')",
        "input[type='button'][value*='Continue' i]",
        "input[type='button'][value*='Next' i]",
        "input[type='submit'][value*='Continue' i]",
        "input[type='submit'][value*='Next' i]",
    ],
    "manual_apply_bypass": [
        "button:has-text('Continue manually')",
        "button:has-text('Apply manually')",
        "button:has-text('Skip')",
        "button:has-text('Continue without LinkedIn')",
        "a:has-text('Continue manually')",
        "a:has-text('Apply manually')",
        "[data-automation-id*='manual' i]",
    ],
    "cookie_consent": [
        "button:has-text('Accept Cookies')",
        "button:has-text('Accept All')",
        "button:has-text('Accept')",
        "button:has-text('I Agree')",
        "button:has-text('Agree')",
        "[data-automation-id*='accept' i]",
        "button:has-text('Close')",
        "button[aria-label='Close']",
    ],
    "login_page_patterns": [
        "/login",
        "/signin",
        "/auth/login",
        "/candidate/login",
        "/myaccount/login",
    ],
}

# Generic Selectors (used as fallbacks)
GENERIC_SELECTORS = {
    "email_field": [
        "input[type='email']",
        "input[name*='email' i]",
        "input[id*='email' i]",
    ],
    "password_field": [
        "input[type='password']",
    ],
    "first_name_field": [
        "input[name*='firstName' i]",
        "input[id*='firstName' i]",
        "input[placeholder*='First' i]",
    ],
    "last_name_field": [
        "input[name*='lastName' i]",
        "input[id*='lastName' i]",
        "input[placeholder*='Last' i]",
    ],
    "confirm_password_field": [
        "input[name*='confirm' i]",
        "input[id*='confirm' i]",
    ],
    "phone_field": [
        "input[type='tel']",
        "input[name*='phone' i]",
    ],
    "dob_field": [
        "input[name*='dob' i]",
        "input[name*='birthdate' i]",
        "input[name*='birthday' i]",
    ],
    "dob_day_field": [
        "input[name*='birth_day' i]",
        "input[id*='day' i][name*='day' i]",
    ],
    "dob_month_field": [
        "input[name*='birth_month' i]",
        "input[id*='month' i]",
    ],
    "dob_year_field": [
        "input[name*='birth_year' i]",
        "input[id*='year' i]",
    ],
    "login_button": [
        "button:has-text('Sign In')",
        "button:has-text('Log In')",
        "button:has-text('Login')",
        "button[type='submit']",
    ],
    "create_account_button": [
        "button:has-text('Create Account')",
        "a:has-text('Create Account')",
        "button:has-text('Register')",
        "a:has-text('Sign Up')",
    ],
    "register_submit": [
        "button[type='submit']",
        "button:has-text('Create Account')",
        "button:has-text('Register')",
        "button:has-text('Sign Up')",
    ],
    "resume_upload": [
        "input[data-automation-id='resumeUpload']",
        "input[data-automation-id='attachmentUpload']",
        "input[type='file'][accept*='pdf']",
        "input[type='file']",
    ],
    "signup_indicators": [
        "button:has-text('Create Account')",
        "button:has-text('Register')",
        "button:has-text('Sign Up')",
        "a:has-text('Create Account')",
        "a:has-text('Sign Up')",
        "h1:has-text('Create Account')",
        "h2:has-text('Register')",
    ],
}

# ============================================================================
# Field Mapping for Application Forms
# ============================================================================
WORKDAY_FIELD_MAPPINGS = {
    "firstName": "first_name",
    "lastName": "last_name",
    "email": "email",
    "phone": "phone",
    "addressLine1": "city",
    "city": "city",
    "postalCode": "postal_code",
}

# ============================================================================
# Gemini Configuration
# ============================================================================
GEMINI_MODEL = "gemini-3.1-flash-lite"
GEMINI_NATIVE_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_COMPAT_BASE = "https://generativelanguage.googleapis.com/v1beta/openai"
GEMINI_REQUEST_TIMEOUT = 15  # seconds

# ============================================================================
# Affirmative Keywords for Checkboxes/Radios
# ============================================================================
AFFIRMATIVE_KEYWORDS = ("yes", "agree", "accept", "authorized", "eligible", "confirm")

# ============================================================================
# Affirmative Keywords for Checkboxes/Radios
# ============================================================================
AFFIRMATIVE_KEYWORDS = ("yes", "agree", "accept", "authorized", "eligible", "confirm")

# ============================================================================
# Default Candidate Data (used as template only - actual from config)
# ============================================================================
DEFAULT_CANDIDATE_TEMPLATE = {
    "full_name": "",
    "preferred_name": "",
    "email": "",
    "password": "",
    "phone": "",
    "city": "",
    "province_state": "",
    "country": "",
    "postal_code": "",
    "address": "",
    "dob_day": "",
    "dob_month": "",
    "dob_year": "",
    "dob": "",
    "linkedin_url": "",
    "github_url": "",
    "portfolio_url": "",
    "website_url": "",
}

# ============================================================================
# File Paths
# ============================================================================
def get_applypilot_dir() -> Path:
    """Get the ApplyPilot data directory."""
    import os
    return Path(os.environ.get("APPLYPILOT_DIR", Path.home() / ".applypilot"))

def get_db_path() -> Path:
    """Get the database path, checking local first."""
    local_db = Path("applypilot.db")
    if local_db.exists():
        return local_db
    return get_applypilot_dir() / DB_FILE_NAME

def get_profile_path() -> Path:
    """Get the profile path, checking local first."""
    local_profile = Path("profile.json")
    if local_profile.exists():
        return local_profile
    return get_applypilot_dir() / PROFILE_FILE_NAME

def get_tailored_resumes_dir() -> Path:
    """Get the tailored resumes directory."""
    local_dir = Path("tailored_resumes")
    if local_dir.exists():
        return local_dir
    return get_applypilot_dir() / TAILORED_RESUMES_DIR