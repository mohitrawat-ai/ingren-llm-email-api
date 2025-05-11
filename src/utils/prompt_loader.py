# src/utils/prompt_loader.py
import os
from pathlib import Path
from string import Template
from typing import Dict, Any, Optional


def load_system_prompt(file_path: str) -> str:
    """
    Load system prompt from a file

    Args:
        file_path: Path to the system prompt file

    Returns:
        The system prompt as a string
    """
    base_dir = Path(__file__).resolve().parents[2]
    absolute_path = os.path.join(base_dir, file_path)

    try:
        with open(absolute_path, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"System prompt file not found at {absolute_path}")


def load_user_prompt_template(file_path: str) -> Template:
    """
    Load user prompt template from a file

    Args:
        file_path: Path to the user prompt template file

    Returns:
        A string.Template object for rendering the user prompt
    """
    base_dir = Path(__file__).resolve().parents[2]
    absolute_path = os.path.join(base_dir, file_path)

    try:
        with open(absolute_path, "r") as file:
            template_str = file.read().strip()
            return Template(template_str)
    except FileNotFoundError:
        raise FileNotFoundError(f"User prompt template file not found at {absolute_path}")


# src/utils/prompt_loader.py
def render_user_prompt(template: Template, request_data: Dict[str, Any]) -> str:
    """
    Render a user prompt from a template and request data

    Args:
        template: The user prompt template
        request_data: Email request data containing prospect, company, seller, and CTA info

    Returns:
        The rendered user prompt as a string
    """
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

    # Ensure all template variables have a value to prevent KeyError
    # This adds empty strings for any missing template variables
    for placeholder in template.template.split('$')[1:]:
        # Extract the variable name from the placeholder
        var_name = placeholder.split('}')[0].split()[0]
        if var_name and var_name not in template_data:
            template_data[var_name] = ""

    # Render the template with the data
    try:
        return template.substitute(template_data)
    except KeyError as e:
        # Log the key that's missing
        missing_key = str(e).strip("'")
        print(f"Warning: Missing template key: {missing_key}")
        template_data[missing_key] = ""
        return template.substitute(template_data)