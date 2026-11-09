"""
Bot Facade for ApplyPilot - adapted from Auto_Jobs_Applier_AI_Agent
Coordinates bot state and components.
"""

from src.logging import logger


class AIHawkBotState:
    """Tracks the readiness state of bot components."""

    def __init__(self):
        self.credentials_set = False
        self.api_key_set = False
        self.job_application_profile_set = False
        self.gpt_answerer_set = False
        self.parameters_set = False
        self.logged_in = False

    def reset(self) -> None:
        """Reset all state flags."""
        self.credentials_set = False
        self.api_key_set = False
        self.job_application_profile_set = False
        self.gpt_answerer_set = False
        self.parameters_set = False
        self.logged_in = False

    def validate_state(self, required_keys: list) -> bool:
        """
        Validate that required state flags are set.

        Args:
            required_keys: List of state attribute names to check

        Returns:
            True if all required flags are True
        """
        for key in required_keys:
            if not getattr(self, key, False):
                logger.error(f"Required state not set: {key}")
                return False
        return True


class AIHawkBotFacade:
    """
    Facade coordinating the job application bot components.
    Manages state and delegates to specialized components.
    """

    def __init__(self):
        self.state = AIHawkBotState()
        self.credentials = None
        self.api_key = None
        self.job_application_profile = None
        self.resume = None
        self.gpt_answerer = None
        self.resume_generator = None
        self.parameters = None
        self.job_manager = None
        self.easy_applier = None

    def _validate_non_empty(self, value, name: str) -> None:
        """Validate that a value is not None or empty."""
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError(f"{name} cannot be empty")

    def _ensure_job_profile_and_resume_set(self) -> None:
        """Ensure job profile and resume are set."""
        if not self.state.job_application_profile_set:
            raise RuntimeError("Job application profile not set. Call set_job_application_profile_and_resume() first.")
        if not self.resume:
            raise RuntimeError("Resume not set. Call set_job_application_profile_and_resume() first.")

    def set_credentials(self, email: str, password: str) -> None:
        """Set LinkedIn credentials."""
        self._validate_non_empty(email, "Email")
        self._validate_non_empty(password, "Password")
        self.credentials = {"email": email, "password": password}
        self.state.credentials_set = True
        logger.debug("Credentials set")

    def set_api_key(self, api_key: str) -> None:
        """Set LLM API key."""
        self._validate_non_empty(api_key, "API Key")
        self.api_key = api_key
        self.state.api_key_set = True
        logger.debug("API key set")

    def set_job_application_profile_and_resume(self, profile, resume: str) -> None:
        """
        Set job application profile and resume.

        Args:
            profile: JobApplicationProfile instance
            resume: Path to resume file or resume text
        """
        self._validate_non_empty(profile, "Job Application Profile")
        self._validate_non_empty(resume, "Resume")
        self.job_application_profile = profile
        self.resume = resume
        self.state.job_application_profile_set = True
        logger.debug("Job application profile and resume set")

    def set_gpt_answerer_and_resume_generator(self, answerer, generator) -> None:
        """Set GPT answerer and resume generator."""
        self.gpt_answerer = answerer
        self.resume_generator = generator
        self.state.gpt_answerer_set = True
        logger.debug("GPT answerer and resume generator set")

    def set_parameters(self, parameters: dict) -> None:
        """Set job search and application parameters."""
        self._validate_non_empty(parameters, "Parameters")
        self.parameters = parameters
        self.state.parameters_set = True
        logger.debug("Parameters set")

    def start_login(self) -> bool:
        """
        Start the login process.

        Returns:
            True if login successful
        """
        if not self.state.credentials_set:
            raise RuntimeError("Credentials not set. Call set_credentials() first.")

        if not self.state.api_key_set:
            raise RuntimeError("API key not set. Call set_api_key() first.")

        # Import here to avoid circular imports
        from src.ai_hawk.authenticator import get_authenticator
        from src.utils.chrome_utils import get_chrome_driver

        # Initialize driver if not already
        if not hasattr(self, 'driver') or self.driver is None:
            self.driver = get_chrome_driver()

        # Get authenticator and start login
        authenticator = get_authenticator(self.driver, "linkedin")
        success = authenticator.start()

        if success:
            self.state.logged_in = True
            logger.info("Login completed successfully")
        else:
            logger.error("Login failed")

        return success

    def start_apply(self) -> None:
        """Start the job application process."""
        # Validate required state
        required = [
            "logged_in",
            "job_application_profile_set",
            "gpt_answerer_set",
            "parameters_set",
        ]
        if not self.state.validate_state(required):
            raise RuntimeError("Required components not initialized")

        # Initialize job manager if not already
        if self.job_manager is None:
            from src.ai_hawk.job_manager import AIHawkJobManager
            self.job_manager = AIHawkJobManager(self.driver)
            self.job_manager.set_parameters(self.parameters)
            self.job_manager.set_gpt_answerer(self.gpt_answerer)
            self.job_manager.set_resume_generator_manager(self.resume_generator)

        # Start applying
        logger.info("Starting job application process...")
        self.job_manager.start_applying()

    def start_collect_data(self) -> None:
        """Start data collection (job discovery without applying)."""
        required = [
            "logged_in",
            "job_application_profile_set",
            "gpt_answerer_set",
            "parameters_set",
        ]
        if not self.state.validate_state(required):
            raise RuntimeError("Required components not initialized")

        if self.job_manager is None:
            from src.ai_hawk.job_manager import AIHawkJobManager
            self.job_manager = AIHawkJobManager(self.driver)
            self.job_manager.set_parameters(self.parameters)
            self.job_manager.set_gpt_answerer(self.gpt_answerer)
            self.job_manager.set_resume_generator_manager(self.resume_generator)

        logger.info("Starting job data collection...")
        self.job_manager.start_collecting_data()