# src/api/routes.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from src.api.models import HealthResponse
from src.services.email_generator import EmailGenerator
from src.config import settings

from ingren_api_types import EmailGenerationRequest, EmailGenerationResponse

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

@router.post("/generate-email", response_model=EmailGenerationResponse, tags=["Email"])
async def generate_email(request: EmailGenerationRequest) -> EmailGenerationResponse:
    """
    Generate a personalized email based on provided parameters
    """
    try:
        # Convert Pydantic model to dict for processing
        request_data = request.model_dump(exclude_none=False)

        # Generate the email using our service
        email_data = await email_generator.generate_email(request_data)

        # Return the data as an EmailResponse
        return EmailGenerationResponse(
            theme_used=email_data["theme_used"],
            anchor_signal=email_data["anchor_signal"],
            subject_line=email_data["subject_line"],
            email_body=email_data["email_body"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email generation failed: {str(e)}")