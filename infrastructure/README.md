# Ingren LLM Email API - AWS Lambda Deployment

This project contains a FastAPI application for generating personalized emails using OpenAI's GPT models, deployed to AWS Lambda and API Gateway using Pulumi.

## Architecture

The deployment follows a serverless architecture:

- **AWS Lambda**: Hosts the FastAPI application
- **API Gateway**: Creates a RESTful API endpoint
- **CloudWatch**: Logs and monitors the application

## Getting Started

See the [Deployment Guide](DEPLOYMENT.md) for step-by-step instructions on how to deploy this application.

## Directory Structure

```
.
├── deploy.sh                  # Deployment script
├── deployment_package/        # Generated during deployment
├── infrastructure/            # Pulumi infrastructure code
│   ├── __main__.py            # Main Pulumi program
│   ├── Pulumi.yaml            # Pulumi project configuration
│   └── Pulumi.dev.yaml        # Environment-specific configuration
├── lambda_handler.py          # AWS Lambda handler using Mangum
├── prompts/                   # Prompt templates
│   ├── system_prompt.txt       
│   └── user_prompt_template.txt
├── requirements.txt           # Python dependencies for Lambda
└── src/                       # Application source code
    ├── api/                   # API endpoints
    ├── services/              # Business logic
    └── utils/                 # Utility functions
```

## Features

- Personalized email generation using GPT models
- Serverless architecture for automatic scaling
- Simple API endpoint for email generation
- Integration with OpenAI
- CORS support for browser clients

## Security

The API is secured using API Gateway's API key authentication:

- All requests require an API key sent in the `x-api-key` header
- API usage is monitored and rate-limited through API Gateway usage plans
- API keys can be rotated or revoked as needed for security

When making requests to the API, include the API key in the header:

```bash
curl -X POST https://your-api-url/dev/api/v1/generate-email \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key-here" \
  -d '{
    "prospect": {
      "first_name": "Sarah",
      "last_name": "Johnson",
      "job_title": "VP of Sales"
      // additional fields...
    },
    "company": {
      "company_name": "TechNova Solutions",
      "industry": "SaaS"
      // additional fields...
    }
    // additional fields...
  }'
```

The API key value is exported as `api_key_value` from the Pulumi stack.