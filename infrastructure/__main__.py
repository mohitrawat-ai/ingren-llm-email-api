"""
Pulumi program to deploy the Ingren LLM Email API to AWS Lambda with API Gateway
"""

import pulumi
import pulumi_aws as aws
import json
import os
from pulumi_aws import lambda_, apigateway

# Configuration
config = pulumi.Config()
stack_name = pulumi.get_stack()
project_name = "ingren-email-api"
lambda_name = f"{project_name}-{stack_name}"
api_gateway_name = f"{project_name}-api-{stack_name}"
environment = config.get("environment") or stack_name
lambda_memory = config.get_int("lambda_memory") or 1024
lambda_timeout = config.get_int("lambda_timeout") or 30

# Create an IAM role for the Lambda function
lambda_role = aws.iam.Role(
    f"{project_name}-lambda-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com",
            },
        }],
    }),
)

# Attach the Lambda basic execution policy to the role
lambda_basic_policy_attachment = aws.iam.RolePolicyAttachment(
    f"{project_name}-lambda-basic-policy",
    role=lambda_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
)

# Create a custom policy for CloudWatch logs
cloudwatch_policy = aws.iam.Policy(
    f"{project_name}-cloudwatch-policy",
    description="Policy for detailed CloudWatch logs for Lambda",
    policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }]
    })
)

# Attach the CloudWatch policy to the Lambda role
cloudwatch_policy_attachment = aws.iam.RolePolicyAttachment(
    f"{project_name}-cloudwatch-policy-attachment",
    role=lambda_role.name,
    policy_arn=cloudwatch_policy.arn,
)

# Create an AWS Lambda function that runs our FastAPI application
lambda_function = lambda_.Function(
    lambda_name,
    role=lambda_role.arn,
    runtime="python3.10",
    handler="lambda_handler.handler",
    code=pulumi.AssetArchive({
        ".": pulumi.FileArchive("./deployment_package"),
    }),
    timeout=lambda_timeout,
    memory_size=lambda_memory,
    environment=lambda_.FunctionEnvironmentArgs(
        variables={
            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
            "OPENAI_MODEL": os.environ.get("OPENAI_MODEL", "gpt-4.1-nano"),
            "SYSTEM_PROMPT_PATH": "prompts/system_prompt.txt",
            "USER_PROMPT_TEMPLATE_PATH": "prompts/user_prompt_template.txt",
        },
    ),
)

# Create an API Gateway REST API
rest_api = apigateway.RestApi(
    api_gateway_name,
    description="API Gateway for Ingren LLM Email API",
    api_key_source="HEADER"  # Enable API key in header
)

# Create an API key
api_key = apigateway.ApiKey(
    f"{project_name}-api-key",
    name=f"{project_name}-key-{stack_name}",
    enabled=True
)

# Create a resource for our API endpoints
api_resource = apigateway.Resource(
    "api-resource",
    rest_api=rest_api.id,
    parent_id=rest_api.root_resource_id,
    path_part="api",
)

# Create a v1 resource under api
v1_resource = apigateway.Resource(
    "v1-resource",
    rest_api=rest_api.id,
    parent_id=api_resource.id,
    path_part="v1",
)

# Create only the generate-email resource
generate_email_resource = apigateway.Resource(
    "generate-email-resource",
    rest_api=rest_api.id,
    parent_id=v1_resource.id,
    path_part="generate-email",
)

# Create the POST method for generate-email
generate_email_method = apigateway.Method(
    "generate-email-method",
    rest_api=rest_api.id,
    resource_id=generate_email_resource.id,
    http_method="POST",
    authorization="NONE",
    api_key_required=True  # Require API key for this method
)

# Create integration between the API Gateway method and Lambda
generate_email_integration = apigateway.Integration(
    "generate-email-integration",
    rest_api=rest_api.id,
    resource_id=generate_email_resource.id,
    http_method=generate_email_method.http_method,
    integration_http_method="POST",
    type="AWS_PROXY",
    uri=lambda_function.invoke_arn,
)

# Set up CORS for the generate-email endpoint
cors_options_method = apigateway.Method(
    "generate-email-options",
    rest_api=rest_api.id,
    resource_id=generate_email_resource.id,
    http_method="OPTIONS",
    authorization="NONE",
)

cors_options_integration = apigateway.Integration(
    "generate-email-options-integration",
    rest_api=rest_api.id,
    resource_id=generate_email_resource.id,
    http_method=cors_options_method.http_method,
    type="MOCK",
    request_templates={
        "application/json": '{"statusCode": 200}'
    },
)

# Set up responses for OPTIONS method
options_method_response = apigateway.MethodResponse(
    "options-method-response",
    rest_api=rest_api.id,
    resource_id=generate_email_resource.id,
    http_method="OPTIONS",
    status_code="200",
    response_models={
        "application/json": "Empty",
    },
    response_parameters={
        "method.response.header.Access-Control-Allow-Headers": True,
        "method.response.header.Access-Control-Allow-Methods": True,
        "method.response.header.Access-Control-Allow-Origin": True,
    },
)

options_integration_response = apigateway.IntegrationResponse(
    "options-integration-response",
    rest_api=rest_api.id,
    resource_id=generate_email_resource.id,
    http_method="OPTIONS",
    status_code="200",
    response_parameters={
        "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
        "method.response.header.Access-Control-Allow-Methods": "'OPTIONS,POST'",
        "method.response.header.Access-Control-Allow-Origin": "'*'",
    },
    selection_pattern="",
    depends_on=[options_method_response],
)

# Set up response for POST method
post_method_response = apigateway.MethodResponse(
    "post-method-response",
    rest_api=rest_api.id,
    resource_id=generate_email_resource.id,
    http_method="POST",
    status_code="200",
    response_models={
        "application/json": "Empty",
    },
    response_parameters={
        "method.response.header.Access-Control-Allow-Origin": True,
    },
)

# Create a deployment for the API
deployment = apigateway.Deployment(
    "api-deployment",
    rest_api=rest_api.id,
    # Explicit dependencies to ensure resources are created before deployment
    opts=pulumi.ResourceOptions(depends_on=[
        generate_email_integration,
        options_integration_response,
        post_method_response,
    ]),
)

# Create a stage for the deployment
stage = apigateway.Stage(
    f"{project_name}-stage-{stack_name}",
    rest_api=rest_api.id,
    deployment=deployment.id,
    stage_name=stack_name,
)

# Create a usage plan
usage_plan = apigateway.UsagePlan(
    f"{project_name}-usage-plan",
    name=f"{project_name}-plan-{stack_name}",
    description=f"Usage plan for {project_name} API",
    api_stages=[
        apigateway.UsagePlanApiStageArgs(
            api_id=rest_api.id,
            stage=stage.stage_name,
        )
    ],
    # Optional: Set rate limits
    quota_settings=apigateway.UsagePlanQuotaSettingsArgs(
        limit=500,
        period="DAY",
    ),
    throttle_settings=apigateway.UsagePlanThrottleSettingsArgs(
        burst_limit=10,
        rate_limit=10,
    ),
)

# Associate the API key with the usage plan
usage_plan_key = apigateway.UsagePlanKey(
    f"{project_name}-usage-plan-key",
    key_id=api_key.id,
    key_type="API_KEY",
    usage_plan_id=usage_plan.id,
)

# Grant API Gateway permission to invoke Lambda
lambda_permission = aws.lambda_.Permission(
    "api-gateway-lambda-permission",
    action="lambda:InvokeFunction",
    function=lambda_function.name,
    principal="apigateway.amazonaws.com",
    source_arn=pulumi.Output.concat(
        rest_api.execution_arn, "/*/*"
    ),
)

# Export relevant URLs and the API key
pulumi.export("api_gateway_url", pulumi.Output.concat(
    "https://", rest_api.id, ".execute-api.", aws.get_region().name, ".amazonaws.com/", stage.stage_name, "/"
))
pulumi.export("generate_email_endpoint", pulumi.Output.concat(
    "https://", rest_api.id, ".execute-api.", aws.get_region().name, ".amazonaws.com/", stage.stage_name, "/api/v1/generate-email"
))
pulumi.export("api_key_value", api_key.value)