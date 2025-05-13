# Ingren Email API Deployment Guide

This guide will walk you through deploying the Ingren LLM Email API to AWS Lambda and API Gateway using Pulumi.

## Prerequisites

1. **AWS CLI**: [Install](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) and [configure](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html) the AWS CLI
2. **Pulumi CLI**: [Install Pulumi](https://www.pulumi.com/docs/get-started/install/)
3. **Python 3.10+**: Required for both the application and Pulumi program
4. **OpenAI API key**: You'll need this for the email generation service

## Step 1: Create Prompt Files

Create prompt files that will be used by the email generator:

```bash
mkdir -p prompts
```

Create the system prompt file (`prompts/system_prompt.txt`) and user prompt template file (`prompts/user_prompt_template.txt`) with your desired content.

## Step 2: Set Environment Variables

Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_MODEL="gpt-4o"  # Or your preferred model
```

## Step 3: Run the Deployment Script

Make the deployment script executable:

```bash
chmod +x deploy.sh
```

Run the script:

```bash
./deploy.sh
```

This script will:
1. Create a deployment package with all the necessary code and dependencies
2. Deploy the infrastructure using Pulumi

## Step 4: Test Your API

After successful deployment, Pulumi will output your API Gateway URL for the generate-email endpoint and an API key. You can test it using curl:

```bash
# Store the API key in a variable
API_KEY=$(pulumi stack output api_key_value --stack dev)

# Use the API key when making a request
curl -X POST \
  $(pulumi stack output generate_email_endpoint) \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{
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
      "employee_count": 250,
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
    }
  }'
```

Note that the API key is required for all requests. Without a valid API key, you'll receive a 403 Forbidden response.

## Updating Your Deployment

To update your deployment:

1. Make your code changes
2. Run the deployment script again:
   ```bash
   ./deploy.sh
   ```

## Cleaning Up

To remove all resources when you're done:

```bash
cd infrastructure
pulumi destroy
```

## Troubleshooting

### Viewing Lambda Logs

You can view your Lambda function's logs in CloudWatch through the AWS Console or using the AWS CLI:

```bash
aws logs get-log-events \
  --log-group-name /aws/lambda/ingren-email-api-dev \
  --log-stream-name $(aws logs describe-log-streams \
                       --log-group-name /aws/lambda/ingren-email-api-dev \
                       --order-by LastEventTime \
                       --descending \
                       --limit 1 \
                       --query 'logStreams[0].logStreamName' \
                       --output text)
```

### Common Issues

1. **Timeout errors**: If your function times out, increase the Lambda timeout in the Pulumi configuration (infrastructure/Pulumi.dev.yaml).
2. **Memory errors**: If you're processing large requests, increase the Lambda memory allocation.
3. **Missing environment variables**: Ensure your OPENAI_API_KEY is set correctly before deploying.