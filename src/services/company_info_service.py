# src/services/company_info_service.py
from typing import Dict, Any
import json

from langsmith import traceable
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from src.api.models import CompanyDescriptionResponse
from src.config import settings


class CompanyInfoService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL_WEB_SEARCH

    @traceable
    async def get_company_description(self, company_url: str) -> Dict[str, Any]:
        """
        Generate a company description by searching the web based on the company URL

        Args:
            company_url: URL of the company website

        Returns:
            Dictionary with company information
        """
        try:
            # System prompt to instruct the model to search for company information
            system_prompt = """
            You are a helpful assistant that provides accurate information about companies.
            Use web search to find information when necessary. 
            ALWAYS format your response as a valid JSON object with the following fields:
            - company_name (string, required): Name of the company
            - description (string, required): Detailed description of what the company does
            - industry (string, optional): Industry or sector
            - employee_count (string, optional): Approximate number of employees
            - headquarters (string, optional): Location of headquarters
            - founded_year (string, optional): Year founded
            - products_services (string, optional): Main products or services

            If you cannot find certain information, omit the field rather than providing guesses.
            """

            # User prompt with the company URL
            user_prompt = f"""
            I need information about the company with the website: {company_url}

            Please search the web to find details about this company and return structured information in JSON format 
            with their name, description, industry, size, headquarters, founding year, and main products/services.
            """

            # Call OpenAI API with web search tool
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                web_search_options={},
            )
            print(response.choices[0].message.content)

            # Parse the JSON response
            try:
                company_data = json.loads(response.choices[0].message.content)

                # Ensure required fields are present
                if "company_name" not in company_data:
                    company_data["company_name"] = "Unknown"
                if "description" not in company_data:
                    company_data["description"] = "No description available."

                return company_data
            except json.JSONDecodeError:
                # Fallback if the response is not valid JSON
                return {
                    "company_name": "Unknown",
                    "description": "Could not retrieve company information from the provided URL."
                }
        except Exception as e:
            # Log the error for debugging
            import traceback
            print(f"Error in get_company_description: {str(e)}")
            print(traceback.format_exc())

            # Return a fallback response
            return {
                "company_name": "Error",
                "description": f"An error occurred while retrieving company information: {str(e)}"
            }