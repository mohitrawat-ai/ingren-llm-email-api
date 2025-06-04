"""
Pulumi program to deploy the Ingren LLM Email API to AWS Lambda with API Gateway
"""

import pulumi
import pulumi_aws as aws
import json
import os
from pulumi_aws import lambda_, apigateway
from branch import Branch
import pulumi_command as command
import time
import hashlib


# Configuration
config = pulumi.Config()
stack_name = pulumi.get_stack()
project_name = "ingren-email-api"
lambda_name = f"{project_name}-{stack_name}"
api_gateway_name = f"{project_name}-api-{stack_name}"
environment = config.get("environment") or stack_name
lambda_memory = config.get_int("lambda_memory") or 1024
lambda_timeout = config.get_int("lambda_timeout") or 30
branches = {
    "main": "v1",
    "wip-prompt-v2": "v2",
}
current_branch = config.get("current_branch")
if current_branch is None:
    raise ValueError("Current branch is required")

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


# The "proper" Pulumi way - work with Outputs throughout
def get_existing_versions_as_outputs(function_name_output, version_branches):
    """Return version queries as Outputs (stay in Pulumi world)"""

    def create_version_queries(function_name):
        versions = {}
        for branch_name_version in version_branches:
            cmd = command.local.Command(
                f"get-version-{branch_name_version}",
                create=f"""
                VERSION=$(aws lambda get-alias \
                  --function-name {function_name} \
                  --name {branch_name_version} \
                  --query 'FunctionVersion' \
                  --output text 2>/dev/null)

                if [ "$?" -eq 0 ] && [ "$VERSION" != "None" ] && [ "$VERSION" != "" ]; then
                    echo "$VERSION"
                else
                    echo "$LATEST"
                fi
                """
            )
            versions[branch_name_version] = cmd.stdout.apply(lambda v: v.strip())
        return versions

    return function_name_output.apply(create_version_queries)




# Create an AWS Lambda function that runs our FastAPI application
lambda_function = lambda_.Function(
    lambda_name,
    role=lambda_role.arn,
    runtime="python3.11",
    handler="lambda_handler.handler",
    code=pulumi.AssetArchive({
        ".": pulumi.FileArchive("../deployment_package"),
    }),
    timeout=lambda_timeout,
    memory_size=lambda_memory,
    publish=True,
    environment=lambda_.FunctionEnvironmentArgs(
        variables={
            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
            "OPENAI_MODEL": os.environ.get("OPENAI_MODEL", "gpt-4.1-nano"),
            "SYSTEM_PROMPT_PATH": "prompts/system_prompt.txt",
            "USER_PROMPT_TEMPLATE_PATH": "prompts/user_prompt_template.txt",
            "LANGSMITH_API_KEY": os.environ.get("LANGSMITH_API_KEY"),
            "LANGSMITH_ENDPOINT": os.environ.get("LANGSMITH_ENDPOINT"),
            "LANGSMITH_PROJECT": os.environ.get("LANGSMITH_PROJECT"),
            "LANGSMITH_TRACING": os.environ.get("LANGSMITH_TRACING"),
        },
    ),
)

# Query existing versions BEFORE creating any Branch objects
# Usage
existing_versions_output = get_existing_versions_as_outputs(lambda_function.name, branches.keys())


pulumi.log.info(f"Existing versions: {existing_versions_output}")

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

deployment_resources = []
# Create a branch for each environment
for branch_name, version in branches.items():
    branch = Branch(branch_name, lambda_function, version, existing_versions_output[branch_name])
    alias = branch.create_alias(current_branch)
    resources = branch.create_api_gateway_resources(rest_api, api_resource.id, alias, lambda_function)
    deployment_resources.extend(resources)


# Create a deployment trigger that changes when Lambda function changes
deployment_trigger = pulumi.Output.all(
    lambda_function.version,
    lambda_function.source_code_hash
).apply(lambda args: hashlib.md5(f"{args[0]}-{args[1]}-{time.time()}".encode()).hexdigest()[:8])

# Create a deployment for the API that includes ALL resources
deployment = apigateway.Deployment(
    "api-deployment",
    rest_api=rest_api.id,
    # Force new deployment when Lambda changes
    description=pulumi.Output.concat(
        "Deployment for Lambda version: ",
        lambda_function.version,
        " trigger: ",
        deployment_trigger
    ),
    # Ensure ALL resources from ALL branches are created before deployment
    opts=pulumi.ResourceOptions(
        depends_on=deployment_resources + [lambda_function],
        # Replace deployment when description changes (i.e., when Lambda changes)
        replace_on_changes=["description"]
    ),
)

# Create a stage for the deployment
stage = apigateway.Stage(
    f"{project_name}-stage-{stack_name}",
    rest_api=rest_api.id,
    deployment=deployment.id,
    stage_name=stack_name,
    # Stage variables that get updated when aliases change
    variables={
        "lambdaAlias": lambda_function.version,
        "environment": stack_name,
        "deploymentTrigger": deployment_trigger,  # Add this to force stage updates
    },
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

# Export relevant URLs and the API key
pulumi.export("api_gateway_url", pulumi.Output.concat(
    "https://", rest_api.id, ".execute-api.", aws.get_region().name, ".amazonaws.com/", stage.stage_name, "/"
))
pulumi.export("generate_email_endpoint", pulumi.Output.concat(
    "https://", rest_api.id, ".execute-api.", aws.get_region().name, ".amazonaws.com/", stage.stage_name, "/api/v1/generate-email"
))
pulumi.export("api_key_value", api_key.value)