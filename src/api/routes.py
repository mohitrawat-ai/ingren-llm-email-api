# src/api/routes.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
import time
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

from src.api.models import HealthResponse
from src.services.email_generator import EmailGenerator
from src.config import settings

from ingren_api_types import EmailGenerationRequest, EmailGenerationResponse, Personalization, Attributes, GeneratedEmail

router = APIRouter()
email_generator = EmailGenerator()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint for AWS load balancer
    """
    return HealthResponse(version=settings.API_VERSION)


@router.get("/health/deep", response_model=HealthResponse, tags=["Health"])
async def deep_health_check():
    """
    Deep health check that verifies OpenAI connection
    """
    try:
        # Test OpenAI connection by making a minimal API call
        client = email_generator.client
        client.models.list(limit=1)
        return HealthResponse(version=settings.API_VERSION)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


# Add to src/api/routes.py

from src.api.models import CompanyURLRequest, CompanyDescriptionResponse
from src.services.company_info_service import CompanyInfoService

# Initialize the company info service
company_info_service = CompanyInfoService()

@router.post("/company-description", response_model=CompanyDescriptionResponse, tags=["Company"])
async def get_company_description(request: CompanyURLRequest):
    """
    Get company description and information based on the company URL
    """
    try:
        # Call the company info service to get the description
        company_data = await company_info_service.get_company_description(request.company_url)

        # Return the data as a CompanyDescriptionResponse
        return CompanyDescriptionResponse(
            company_name=company_data.get("company_name", "Unknown"),
            description=company_data.get("description", "No description available."),
            industry=company_data.get("industry"),
            employee_count=company_data.get("employee_count"),
            headquarters=company_data.get("headquarters"),
            founded_year=company_data.get("founded_year"),
            products_services=company_data.get("products_services")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Company information retrieval failed: {str(e)}")

# Other routes...
@router.post("/generate-email", response_model=EmailGenerationResponse, tags=["Email Generation"])
async def generate_email(request: EmailGenerationRequest) -> EmailGenerationResponse:
    """
    Generate a personalized email based on provided parameters
    """
    start_time = time.time()

    try:
        # Validate minimum required data
        if not request.prospect.name or not request.prospect.company:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": {
                        "code": "insufficient_data",
                        "message": "Minimum prospect data required: name, company",
                        "fallback": {
                            "subject": "Quick question about your team",
                            "body": "Hi there,\n\nI hope this email finds you well...\n\nBest regards,\n[Your Name]",
                            "wordCount": 12
                        }
                    }
                }
            )

        # Convert request to format expected by email generator
        email_data = await email_generator.generate_email(request)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Count words in email body
        word_count = len(email_data["email_body"].split())

        # Calculate email score (simple heuristic for now)
        # TODO : Add logic to calculate email score, using LLM as a Judge
        email_score = 50

        return EmailGenerationResponse(
            success=True,
            email=GeneratedEmail(
                subject=email_data["subject_line"],
                body=email_data["email_body"],
                wordCount=word_count
            ),
            personalization=Personalization(
                elementsUsed=email_data.get("personalization_elements", []),
                primaryPersonalization=email_data.get("anchor_signal", "unknown"),
                confidence=email_data.get("personalization_confidence", 0.5)   # Default confidence score
            ),
            attributes=Attributes(
                generatedAt=datetime.now().isoformat() + "Z",
                processingTimeMs=processing_time_ms,
                emailScore=email_score
            )
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Email generation error: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "llm_error",
                    "message": "Email generation service temporarily unavailable"
                }
            }
        )