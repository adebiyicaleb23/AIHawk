"""
LLM Manager for ApplyPilot - adapted from Auto_Jobs_Applier_AI_Agent
Handles multiple LLM providers and provides high-level answerer interface.
"""

import os
import json
import time
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

# Perplexity import - handle version differences
try:
    from langchain_community.chat_models import ChatPerplexity
except ImportError:
    try:
        from langchain_perplexity import ChatPerplexity
    except ImportError:
        ChatPerplexity = None

from config import (
    LLM_MODEL_TYPE,
    LLM_MODEL,
    LLM_API_URL,
)
from constants import (
    OPENAI,
    CLAUDE,
    OLLAMA,
    GEMINI,
    PERPLEXITY,
    HUGGINGFACE,
)
from src.logging import logger


class AIModel(ABC):
    """Abstract base class for LLM models."""

    @abstractmethod
    def get_model(self) -> BaseChatModel:
        """Get the configured LangChain chat model."""
        pass


class OpenAIModel(AIModel):
    """OpenAI model configuration."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", api_url: str = None):
        self.api_key = api_key
        self.model = model
        self.api_url = api_url or "https://api.openai.com/v1"

    def get_model(self) -> BaseChatModel:
        return ChatOpenAI(
            api_key=self.api_key,
            model=self.model,
            base_url=self.api_url,
            temperature=0.3,
            max_tokens=2000,
        )


class ClaudeModel(AIModel):
    """Anthropic Claude model configuration."""

    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        self.api_key = api_key
        self.model = model

    def get_model(self) -> BaseChatModel:
        return ChatAnthropic(
            api_key=self.api_key,
            model=self.model,
            temperature=0.3,
            max_tokens=2000,
        )


class OllamaModel(AIModel):
    """Local Ollama model configuration."""

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def get_model(self) -> BaseChatModel:
        return ChatOllama(
            model=self.model,
            base_url=self.base_url,
            temperature=0.3,
        )


class GeminiModel(AIModel):
    """Google Gemini model configuration."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model

    def get_model(self) -> BaseChatModel:
        return ChatGoogleGenerativeAI(
            google_api_key=self.api_key,
            model=self.model,
            temperature=0.3,
            max_output_tokens=2000,
        )


class PerplexityModel(AIModel):
    """Perplexity model configuration."""

    def __init__(self, api_key: str, model: str = "llama-3.1-sonar-small-128k-online"):
        self.api_key = api_key
        self.model = model

    def get_model(self) -> BaseChatModel:
        if ChatPerplexity is None:
            raise ImportError("ChatPerplexity not available. Install langchain-perplexity or use older langchain_community.")
        return ChatPerplexity(
            api_key=self.api_key,
            model=self.model,
            temperature=0.3,
            max_tokens=2000,
        )


class AIAdapter:
    """Factory for creating LLM model instances."""

    @staticmethod
    def get_model(model_type: str = None, **kwargs) -> BaseChatModel:
        """
        Get LLM model based on type.

        Args:
            model_type: Type of model (openai, claude, ollama, gemini, perplexity)
            **kwargs: Additional arguments (api_key, model, base_url)

        Returns:
            Configured LangChain chat model
        """
        model_type = model_type or LLM_MODEL_TYPE
        api_key = kwargs.get("api_key") or os.getenv("LLM_API_KEY")
        model = kwargs.get("model") or LLM_MODEL
        base_url = kwargs.get("base_url") or LLM_API_URL

        if model_type == OPENAI:
            return OpenAIModel(api_key, model, base_url).get_model()
        elif model_type == CLAUDE:
            return ClaudeModel(api_key, model).get_model()
        elif model_type == OLLAMA:
            return OllamaModel(model, base_url).get_model()
        elif model_type == GEMINI:
            return GeminiModel(api_key, model).get_model()
        elif model_type == PERPLEXITY:
            return PerplexityModel(api_key, model).get_model()
        else:
            raise ValueError(f"Unsupported model type: {model_type}")


class LoggerChatModel:
    """
    Wrapper that logs LLM requests/responses for debugging and cost tracking.
    """

    def __init__(self, model: BaseChatModel, log_dir: Path = None):
        self.model = model
        self.log_dir = log_dir or Path("data_folder/output")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "llm_calls.json"
        self.total_tokens = 0
        self.total_cost = 0.0

    def invoke(self, messages: List, **kwargs) -> Any:
        """Invoke the model with logging."""
        start_time = time.time()

        # Log request
        request_log = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model": getattr(self.model, "model_name", "unknown"),
            "messages": [{"role": m.type, "content": m.content} for m in messages],
            "kwargs": kwargs,
        }

        try:
            response = self.model.invoke(messages, **kwargs)

            # Log response
            response_log = {
                "response": response.content,
                "usage": getattr(response, "usage_metadata", {}),
                "response_time": time.time() - start_time,
            }

            # Update token tracking
            usage = response_log["usage"]
            if usage:
                self.total_tokens += usage.get("total_tokens", 0)
                # Rough cost estimation (update with actual pricing)
                self.total_cost += usage.get("total_tokens", 0) * 0.00001

            # Combine and save
            full_log = {**request_log, **response_log}
            self._save_log(full_log)

            return response

        except Exception as e:
            error_log = {**request_log, "error": str(e)}
            self._save_log(error_log)
            raise

    def _save_log(self, log_entry: Dict) -> None:
        """Save log entry to file."""
        try:
            logs = []
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)

            logs.append(log_entry)

            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Failed to save LLM log: {e}")


class GPTAnswerer:
    """
    High-level interface for answering job application questions.
    """

    def __init__(self, model: BaseChatModel = None, log_dir: Path = None):
        if model is None:
            model = AIAdapter.get_model()
        self.model = LoggerChatModel(model, log_dir)

        # Import prompts
        from src.ai_hawk.llm.prompts import (
            SUMMARIZE_JOB_DESCRIPTION,
            GENERATE_COVER_LETTER,
            ANSWER_NUMERIC_QUESTION,
            ANSWER_MULTIPLE_CHOICE,
            ANSWER_FREE_TEXT,
            SCORE_JOB_SUITABILITY,
        )
        self.prompts = {
            "summarize": SUMMARIZE_JOB_DESCRIPTION,
            "cover_letter": GENERATE_COVER_LETTER,
            "numeric": ANSWER_NUMERIC_QUESTION,
            "multiple_choice": ANSWER_MULTIPLE_CHOICE,
            "free_text": ANSWER_FREE_TEXT,
            "score": SCORE_JOB_SUITABILITY,
        }

    def summarize_job(self, job_description: str) -> str:
        """Summarize a job description."""
        prompt = self.prompts["summarize"].format(job_description=job_description)
        response = self.model.invoke([HumanMessage(content=prompt)])
        return response.content.strip()

    def generate_cover_letter(
        self,
        job_description: str,
        resume: str,
        company: str,
        position: str
    ) -> str:
        """Generate a tailored cover letter."""
        prompt = self.prompts["cover_letter"].format(
            job_description=job_description,
            resume=resume,
            company=company,
            position=position
        )
        response = self.model.invoke([HumanMessage(content=prompt)])
        return response.content.strip()

    def answer_question(
        self,
        question: str,
        job_description: str = "",
        resume: str = "",
        question_type: str = "free_text",
        options: List[str] = None
    ) -> str:
        """
        Answer a job application question.

        Args:
            question: The question text
            job_description: Job description for context
            resume: Resume text for context
            question_type: Type of question (numeric, multiple_choice, free_text)
            options: Options for multiple choice questions

        Returns:
            Answer string
        """
        if question_type == "numeric":
            prompt = self.prompts["numeric"].format(
                question=question,
                job_description=job_description,
                resume=resume
            )
        elif question_type == "multiple_choice" and options:
            prompt = self.prompts["multiple_choice"].format(
                question=question,
                options="\n".join(options),
                job_description=job_description,
                resume=resume
            )
        else:
            prompt = self.prompts["free_text"].format(
                question=question,
                job_description=job_description,
                resume=resume
            )

        response = self.model.invoke([HumanMessage(content=prompt)])
        return response.content.strip()

    def score_job_suitability(
        self,
        job_description: str,
        resume: str,
        work_preferences: Dict = None
    ) -> int:
        """
        Score job suitability from 1-10.

        Returns:
            Suitability score (1-10)
        """
        preferences_text = ""
        if work_preferences:
            preferences_text = f"\nWork Preferences: {json.dumps(work_preferences)}"

        prompt = self.prompts["score"].format(
            job_description=job_description,
            resume=resume,
            preferences=preferences_text
        )

        response = self.model.invoke([HumanMessage(content=prompt)])

        try:
            score = int(response.content.strip())
            return max(1, min(10, score))  # Clamp to 1-10
        except ValueError:
            logger.warning(f"Invalid score response: {response.content}")
            return 5  # Default middle score