"""
Lambda handler for the Ingren LLM Email API using Mangum to adapt FastAPI to AWS Lambda
"""

from mangum import Mangum
from src.main import app

# Create the Mangum handler
handler = Mangum(app)