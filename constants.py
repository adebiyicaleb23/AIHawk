"""
Constants module for ApplyPilot - adapted from Auto_Jobs_Applier_AI_Agent
"""

# Config file names
SECRETS_YAML = "secrets.yaml"
WORK_PREFERENCES_YAML = "work_preferences.yaml"
PLAIN_TEXT_RESUME_YAML = "plain_text_resume.yaml"

# Log Levels
DEBUG = "DEBUG"
INFO = "INFO"
WARNING = "WARNING"
ERROR = "ERROR"
CRITICAL = "CRITICAL"
MINIMUM_LOG_LEVEL = INFO

# LLM Usage Tracking Keys
USAGE_METADATA = "usage_metadata"
INPUT_TOKENS = "input_tokens"
OUTPUT_TOKENS = "output_tokens"
TOTAL_TOKENS = "total_tokens"
TOKEN_USAGE = "token_usage"
TOTAL_COST = "total_cost"
RESPONSE_METADATA = "response_metadata"
MODEL_NAME = "model_name"
SYSTEM_FINGERPRINT = "system_fingerprint"
FINISH_REASON = "finish_reason"
LOGPROBS = "logprobs"

# LLM Providers
OPENAI = "openai"
CLAUDE = "claude"
OLLAMA = "ollama"
GEMINI = "gemini"
HUGGINGFACE = "huggingface"
PERPLEXITY = "perplexity"

# Data Keys for Job Applications
PROMPTS = "prompts"
REPLIES = "replies"
CONTENT = "content"
RESUME = "resume"
JOB_DESCRIPTION = "job_description"
COMPANY = "company"
COVER_LETTER = "cover_letter"
PERSONAL_INFORMATION = "personal_information"
WORK_PREFERENCES = "work_preferences"
EDUCATION_DETAILS = "education_details"
EXPERIENCE_DETAILS = "experience_details"
PROJECTS = "projects"
AVAILABILITY = "availability"
SALARY_EXPECTATIONS = "salary_expectations"
CERTIFICATIONS = "certifications"
LANGUAGES = "languages"
INTERESTS = "interests"
SELF_IDENTIFICATION = "self_identification"
LEGAL_AUTHORIZATION = "legal_authorization"

# Model Configuration Keys
LLM_MODEL_TYPE = "llm_model_type"
LLM_API_URL = "llm_api_url"
LLM_MODEL = "llm_model"