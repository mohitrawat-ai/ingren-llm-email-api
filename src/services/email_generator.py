# src/services/email_generator.py
import json
from typing import Dict, Any

from langsmith import traceable
from langsmith.wrappers import wrap_openai
from openai import OpenAI

from src.config import settings
from src.utils.prompt_loader import (
    load_system_prompt,
    load_user_prompt_template,
    render_user_prompt
)


class EmailGenerator:
    def __init__(self):
        self.client = wrap_openai(OpenAI(api_key=settings.OPENAI_API_KEY))
        self.system_prompt = load_system_prompt(settings.SYSTEM_PROMPT_PATH)
        self.user_prompt_template = load_user_prompt_template(
            settings.USER_PROMPT_TEMPLATE_PATH
        )
        self.model = settings.OPENAI_MODEL

    @traceable
    async def generate_email(
            self,
            request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a personalized email using the LLM

        Args:
            request_data: Complete request data with prospect, company, etc.

        Returns:
            The generated email data as a dictionary
        """
        try:
            # Ensure request_data is a dictionary
            if request_data is None:
                request_data = {}

            # Ensure required sections exist
            if "prospect" not in request_data:
                request_data["prospect"] = {}
            if "company" not in request_data:
                request_data["company"] = {}

            # Render the user prompt using the template and input data
            user_prompt = render_user_prompt(
                self.user_prompt_template,
                request_data
            )

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
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