from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # API settings
    API_TITLE: str = "Ingren LLM Email API"
    API_DESCRIPTION: str = "API for generating personalized emails using LLMs"
    API_VERSION: str = "0.1.0"

    # OpenAI settings
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4.1-nano"
    OPENAI_MODEL_WEB_SEARCH: str = "gpt-4o-mini-search-preview"

    # Prompt settings
    SYSTEM_PROMPT_PATH: str = "prompts/system_prompt.txt"
    USER_PROMPT_TEMPLATE_PATH: str = "prompts/user_prompt_template.txt"

    # LangSmith settings
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_PROJECT: str = "ingren-emails"
    LANGSMITH_TRACING: str = "true"
    LANGSMITH_SYSTEM_PROMPT_ID: Optional[str] = "ingren_email_system"
    LANGSMITH_USER_PROMPT_ID: Optional[str] = "ingren_email_user"
    LANGSMITH_USER_FOLLOWUP_PROMPT_ID: Optional[str] = "ingren_email_followup"

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Replace the old class Config with model_config
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }


settings = Settings()