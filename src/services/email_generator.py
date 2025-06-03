# src/services/email_generator.py
import json
from typing import Dict, Any

from ingren_api_types import EmailGenerationRequest
from langsmith import traceable
from langsmith.wrappers import wrap_openai
from openai import OpenAI

from src.config import settings
from src.utils.langsmith_prompt_manager import LangsmithPromptManager


class EmailGenerator:
    def __init__(self):
        self.client = wrap_openai(OpenAI(api_key=settings.OPENAI_API_KEY))
        self.prompt_manager = LangsmithPromptManager()
        self.model = settings.OPENAI_MODEL

    @traceable
    async def generate_email(
            self,
            request: EmailGenerationRequest
    ) -> Dict[str, Any]:
        """
        Generate a personalized email using the LLM

        Args:
            request: Complete request data with prospect, company, etc.

        Returns:
            The generated email data as a dictionary
        """
        try:
            request_data = {
                "prospect": request.prospect.model_dump() if request.prospect else {},
                "company": request.company.model_dump() if request.company else {},
                "employment": request.employment.model_dump() if request.employment else {},
                "campaign": request.campaign.model_dump() if request.campaign else {},
                "context": request.context.model_dump() if request.context else {}
            }

            # Render both prompts using the LangsmithPromptManager
            prompts = self.prompt_manager.render_prompt(
                request_data,
                user_prompt_id=settings.LANGSMITH_USER_PROMPT_ID,
                system_prompt_id=settings.LANGSMITH_SYSTEM_PROMPT_ID
            )

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompts["system_prompt"]},
                    {"role": "user", "content": prompts["user_prompt"]}
                ],
                store=True,
                temperature=0.7,
                max_tokens=1500,
                response_format={"type": "json_object"}  # Enforce JSON response
            )

            # Parse the JSON response
            try:
                email_data = json.loads(response.choices[0].message.content)
                return email_data
            except json.JSONDecodeError:
                # Fallback if the response is not valid JSON
                return {
                    "theme_used": "unknown",
                    "anchor_signal": "unknown",
                    "subject_line": "Error in generation",
                    "email_body": response.choices[0].message.content
                }
        except Exception as e:
            # Log the error for debugging
            import traceback
            print(f"Error in generate_email: {str(e)}")
            print(traceback.format_exc())

            # Return a fallback response
            return {
                "theme_used": "error",
                "anchor_signal": "error",
                "subject_line": "Error in email generation",
                "email_body": f"An error occurred during email generation: {str(e)}"
            }