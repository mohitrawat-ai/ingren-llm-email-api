# src/api/models.py
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str


class ProspectData(BaseModel):
    first_name: str = Field(..., description="Prospect's first name")
    last_name: str = Field(..., description="Prospect's last name")
    job_title: str = Field(..., description="Prospect's job title")
    department: Optional[str] = Field(None, description="Department (Sales/RevOps/etc.)")
    tenure_months: Optional[int] = Field(None, description="Months in current role")
    notable_achievement: Optional[str] = Field(None, description="Optional notable achievement")


class CompanyData(BaseModel):
    company_name: str = Field(..., description="Company name")
    industry: Optional[str] = Field(None, description="Industry sector")
    employee_count: Optional[str] = Field(None, description="Number of employees")
    annual_revenue: Optional[str] = Field(None, description="Annual revenue")
    funding_stage: Optional[str] = Field(None, description="Funding stage (Seed/Series A/etc.)")
    growth_signals: Optional[str] = Field(None, description="Recent growth indicators")
    recent_news: Optional[str] = Field(None, description="Recent company news or empty string")
    technography: Optional[str] = Field(None, description="Tools and technologies used")
    description: Optional[str] = Field(None, description="Brief company description")


class SellerData(BaseModel):
    product_name: str = Field("Ingren.ai", description="Product name")
    category: str = Field("AI‑powered outbound automation", description="Product category")
    headline_benefit: str = Field(
        "Turns 8 hrs of prospect research into 8 min",
        description="Main benefit headline"
    )
    unique_proof: str = Field(
        "87% faster research → 22% more first‑call bookings",
        description="Proof point with metrics"
    )
    marquee_case_studies: Optional[str] = Field(None, description="Brief case study highlights")


class CTAData(BaseModel):
    ask: Optional[str] = Field(None, description="Call to action ask (e.g., '15-min chat next week?')")
    calendar_link: Optional[str] = Field(None, description="Meeting scheduling link")


class EmailRequest(BaseModel):
    prospect: ProspectData
    company: CompanyData
    seller: Optional[SellerData] = Field(
        default=None,
        description="Seller information (defaults provided if not specified)"
    )
    cta: Optional[CTAData] = Field(
        default=None,
        description="Call to action details"
    )
    email_tone: Optional[str] = Field(
        default="professional",
        description="Email tone (defaults provided if not specified)"
    )

    sender_name: Optional[str] = Field(
        default=None,
        description="Sender Email name to be used in signature"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prospect": {
                        "first_name": "Sarah",
                        "last_name": "Johnson",
                        "job_title": "VP of Sales",
                        "department": "Sales",
                        "tenure_months": 18,
                        "notable_achievement": "Exceeded Q1 targets by 27%"
                    },
                    "company": {
                        "company_name": "TechNova Solutions",
                        "industry": "SaaS",
                        "employee_count": "250",
                        "annual_revenue": "$45M",
                        "funding_stage": "Series B",
                        "growth_signals": "30% YoY growth, hiring burst in sales",
                        "recent_news": "Launched new enterprise product line",
                        "technography": "Salesforce, Marketo, Outreach.io",
                        "description": "Cloud-based project management software"
                    },
                    "cta": {
                        "ask": "15-min chat next Tuesday?",
                        "calendar_link": "calendly.com/ingren/demo"
                    },
                    "email_tone": "professional",
                    "sender_name": "John Doe"
                }
            ]
        }
    }


class EmailResponse(BaseModel):
    theme_used: str = Field(..., description="The outbound theme used for the email")
    anchor_signal: str = Field(..., description="The key fact/pain triggering outreach")
    subject_line: str = Field(..., description="The email subject line")
    email_body: str = Field(..., description="The generated email body text")