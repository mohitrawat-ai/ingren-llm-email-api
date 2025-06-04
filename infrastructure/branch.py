from pulumi_aws import lambda_, apigateway
import pulumi
import pulumi_command as command


class Branch:
    def __init__(self, name, lambda_function, version, current_lambda_version):
        self.name = name
        self.is_main_branch = name == "main"
        self.lambda_function = lambda_function
        self.version = version
        self.current_lambda_version = current_lambda_version

    def create_alias(self, current_branch):# For feature branches - always update alias to current $LATEST

        if self.name == current_branch:
            function_version = self.lambda_function.version
        else:
            # existing_versions[self.name] is an Output, that's fine!
            function_version = self.current_lambda_version

        lambda_alias = lambda_.Alias(
            f"lambda-alias-{self.name}",
            function_name=self.lambda_function.name,
            function_version=function_version,
            name=self.name,
        )
        return lambda_alias

    def create_api_gateway_resources(self, rest_api, parent_id, lambda_alias, lambda_function):
        # Create a version resource under api
        v_resource = apigateway.Resource(
            f"version-resource-{self.name}",
            rest_api=rest_api.id,
            parent_id=parent_id,
            path_part=self.version,
        )
        # Create only the generate-email resource
        generate_email_resource = apigateway.Resource(
            f"generate-email-resource-{self.name}",
            rest_api=rest_api.id,
            parent_id=v_resource.id,
            path_part="generate-email",
        )

        # Create the POST method for generate-email
        generate_email_method = apigateway.Method(
            f"generate-email-method-{self.name}",
            rest_api=rest_api.id,
            resource_id=generate_email_resource.id,
            http_method="POST",
            authorization="NONE",
            api_key_required=True  # Require API key for this method
        )

        # Create integration between the API Gateway method and Lambda
        generate_email_integration = apigateway.Integration(
            f"generate-email-integration-{self.name}",
            rest_api=rest_api.id,
            resource_id=generate_email_resource.id,
            http_method=generate_email_method.http_method,
            integration_http_method="POST",
            type="AWS_PROXY",
            uri=pulumi.Output.concat(lambda_alias.invoke_arn),
        )

        # Set up CORS for the generate-email endpoint
        cors_options_method = apigateway.Method(
            f"generate-email-options-{self.name}",
            rest_api=rest_api.id,
            resource_id=generate_email_resource.id,
            http_method="OPTIONS",
            authorization="NONE",
        )

        cors_options_integration = apigateway.Integration(
            f"generate-email-options-integration-{self.name}",
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
            "options-method-response" + self.name,
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
            f"options-integration-response-{self.name}",
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
            opts=pulumi.ResourceOptions(depends_on=[options_method_response]),

        )

        # Set up response for POST method
        post_method_response = apigateway.MethodResponse(
            f"post-method-response-{self.name}",
            rest_api=rest_api.id,
            resource_id=generate_email_resource.id,
            http_method=generate_email_method.http_method,
            status_code="200",
            response_models={
                "application/json": "Empty",
            },
            response_parameters={
                "method.response.header.Access-Control-Allow-Origin": True,
            },
        )

        # Grant API Gateway permission to invoke Lambda
        lambda_permission = lambda_.Permission(
            f"api-gateway-lambda-permission-{self.name}",
            action="lambda:InvokeFunction",
            function=lambda_function.name,
            principal="apigateway.amazonaws.com",
            qualifier=lambda_alias.name,
            source_arn=pulumi.Output.concat(
                rest_api.execution_arn, "/*/*"
            ),
        )

        resources = [
            v_resource,
            generate_email_resource,
            generate_email_method,
            generate_email_integration,
            cors_options_method,
            cors_options_integration,
            options_method_response,
            options_integration_response,
            post_method_response,
            lambda_permission
        ]

        return resources

