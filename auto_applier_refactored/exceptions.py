"""
ApplyPilot Exception Hierarchy

Structured exceptions for better error handling and debugging.
"""


class ApplyPilotError(Exception):
    """Base exception for all ApplyPilot errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigurationError(ApplyPilotError):
    """Raised when configuration is missing or invalid."""

    def __init__(self, message: str, missing_fields: list[str] | None = None):
        details = {"missing_fields": missing_fields} if missing_fields else {}
        super().__init__(message, details)
        self.missing_fields = missing_fields or []


class AuthenticationError(ApplyPilotError):
    """Raised when portal authentication fails."""

    def __init__(self, message: str, portal: str | None = None, url: str | None = None):
        details = {}
        if portal:
            details["portal"] = portal
        if url:
            details["url"] = url
        super().__init__(message, details)
        self.portal = portal
        self.url = url


class NavigationError(ApplyPilotError):
    """Raised when page navigation or URL resolution fails."""

    def __init__(self, message: str, url: str | None = None, selector: str | None = None):
        details = {}
        if url:
            details["url"] = url
        if selector:
            details["selector"] = selector
        super().__init__(message, details)
        self.url = url
        self.selector = selector


class FormFillError(ApplyPilotError):
    """Raised when form filling or submission fails."""

    def __init__(self, message: str, field_name: str | None = None, selector: str | None = None):
        details = {}
        if field_name:
            details["field_name"] = field_name
        if selector:
            details["selector"] = selector
        super().__init__(message, details)
        self.field_name = field_name
        self.selector = selector


class GeminiError(ApplyPilotError):
    """Raised when Gemini API calls fail."""

    def __init__(self, message: str, status_code: int | None = None, model: str | None = None):
        details = {}
        if status_code:
            details["status_code"] = status_code
        if model:
            details["model"] = model
        super().__init__(message, details)
        self.status_code = status_code
        self.model = model


class DatabaseError(ApplyPilotError):
    """Raised when database operations fail."""

    def __init__(self, message: str, operation: str | None = None, query: str | None = None):
        details = {}
        if operation:
            details["operation"] = operation
        if query:
            details["query"] = query[:200] if query else None  # Truncate for safety
        super().__init__(message, details)
        self.operation = operation
        self.query = query


class ProfileLoadError(ConfigurationError):
    """Raised when candidate profile cannot be loaded."""

    def __init__(self, message: str, profile_path: str | None = None):
        details = {"profile_path": profile_path} if profile_path else {}
        super().__init__(message, details)
        self.profile_path = profile_path


class ResumeNotFoundError(ApplyPilotError):
    """Raised when tailored resume file is not found."""

    def __init__(self, message: str, resume_path: str | None = None):
        details = {"resume_path": resume_path} if resume_path else {}
        super().__init__(message, details)
        self.resume_path = resume_path


class SelectorNotFoundError(NavigationError):
    """Raised when a required selector is not found on page."""

    def __init__(self, selector: str, page_url: str):
        super().__init__(
            f"Required selector not found: {selector}",
            url=page_url,
            selector=selector
        )