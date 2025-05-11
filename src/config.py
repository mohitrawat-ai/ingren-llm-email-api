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
    OPENAI_MODEL: str = "gpt-4o"

    # Prompt settings
    SYSTEM_PROMPT_PATH: str = "prompts/system_prompt.txt"
    USER_PROMPT_TEMPLATE_PATH: str = "prompts/user_prompt_template.txt"

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