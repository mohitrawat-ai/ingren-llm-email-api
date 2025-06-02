# src/utils/langsmith_prompt_manager.py
import os
from typing import Dict, Any, Optional
from langsmith import Client
import json
from string import Template

from langsmith.client import convert_prompt_to_openai_format

from src.config import settings


class LangsmithPromptManager:
    """
    Singleton class for managing prompts using LangSmith.
    Loads prompts from LangSmith and handles variable replacement.
    """
    _instance = None
    _client = None
    _system_prompt = None
    _user_prompt_template = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LangsmithPromptManager, cls).__new__(cls)
            cls._initialize()
        return cls._instance

    @classmethod
    def _initialize(cls):
        """Initialize the LangSmith client and load prompts"""
        cls._client = Client()
        # Prompts will be loaded on demand

    @classmethod
    def get_system_prompt(cls, prompt_id: Optional[str] = None) -> str:
        """
        Get system prompt from LangSmith by ID or use cached version

        Args:
            prompt_id: Optional ID of the prompt in LangSmith

        Returns:
            The system prompt as a string
        """
        # Return cached version or try to load from environment
        if cls._system_prompt:
            return cls._system_prompt

        if prompt_id:
            try:
                prompt = cls._client.pull_prompt(prompt_id, include_model=False)
                prompt_value = prompt.invoke({})
                openai_payload = convert_prompt_to_openai_format(prompt_value)
                cls._system_prompt = openai_payload["messages"][0]["content"]
                return cls._system_prompt
            except Exception as e:
                print(f"Error loading system prompt from LangSmith: {str(e)}")
                # Fall back to cached version if available
                if cls._system_prompt:
                    return cls._system_prompt
                return "You are an AI assistant that helps generate personalized emails."


        # Default fallback
        return "You are an AI assistant that helps generate personalized emails."

    @classmethod
    def get_user_prompt_template(cls, prompt_id: Optional[str] = None):
        """
        Get user prompt template from LangSmith by ID or use cached version

        Args:
            prompt_id: Optional ID of the prompt in LangSmith

        Returns:
            A string.Template object for rendering the user prompt
        """
        # Return cached version or try to load from environment
        if cls._user_prompt_template:
            return cls._user_prompt_template

        if prompt_id:
            try:
                prompt = cls._client.pull_prompt(prompt_id, include_model=False)
                cls._user_prompt_template = prompt
                return cls._user_prompt_template
            except Exception as e:
                print(f"Error loading user prompt template from LangSmith: {str(e)}")
                # Fall back to cached version if available
                if cls._user_prompt_template:
                    return cls._user_prompt_template
                return "Write a personalized email"

        # Default fallback
        return "Write a personalized email."

    @classmethod
    def render_prompt(cls, request_data: Dict[str, Any],
                      user_prompt_id: Optional[str] = None,
                      system_prompt_id: Optional[str] = None) -> Dict[str, str]:
        """
        Render both system and user prompts using the request data

        Args:
            request_data: Email request data containing prospect, company, etc.
            user_prompt_id: Optional ID of the user prompt in LangSmith
            system_prompt_id: Optional ID of the system prompt in LangSmith

        Returns:
            Dictionary with rendered 'system_prompt' and 'user_prompt'
        """
        # Get templates
        system_prompt = cls.get_system_prompt(system_prompt_id)
        user_prompt_template = cls.get_user_prompt_template(user_prompt_id)

        # Create a flat dictionary for template substitution
        template_data = {}

        # Add prospect data (ensure it's not None)
        prospect = request_data.get("prospect", {}) or {}
        for key, value in prospect.items():
            template_data[f"prospect_{key}"] = str(value) if value is not None else ""

        # Add company data (ensure it's not None)
        company = request_data.get("company", {}) or {}
        for key, value in company.items():
            template_data[f"company_{key}"] = str(value) if value is not None else ""

        # Add seller data with defaults (ensure it's not None)
        default_seller = {
            "product_name": "Ingren.ai",
            "category": "AI‑powered outbound automation",
            "headline_benefit": "Turns 8 hrs of prospect research into 8 min",
            "unique_proof": "87% faster research → 22% more first‑call bookings",
            "marquee_case_studies": ""
        }
        seller = request_data.get("seller") or {}
        seller_data = {**default_seller, **seller}
        for key, value in seller_data.items():
            template_data[f"seller_{key}"] = str(value) if value is not None else ""

        # Add CTA data (ensure it's not None)
        cta = request_data.get("cta", {}) or {}
        for key, value in cta.items():
            template_data[f"cta_{key}"] = str(value) if value is not None else ""

        # Replace sender_name and email_tone from root object
        template_data["sender_name"] = request_data.get("sender_name", "Ingren AI")
        template_data["email_tone"] = request_data.get("email_tone", "professional")

        user_prompt_invoked = user_prompt_template.invoke(template_data)

        openai_payload = convert_prompt_to_openai_format(user_prompt_invoked)
        user_prompt = openai_payload["messages"][0]["content"]


        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }