from aws_cdk import (
    # Duration,
    Tags,
    Stack,
    aws_lambda as lambda_,
    aws_lambda_python_alpha as lambda_python,
    aws_apigateway as apigateway,
    aws_ssm as ssm, 
    aws_iam as iam,
    aws_logs as logs,
    CfnParameter,
    Duration
)
from constructs import Construct
import json

RESOURCE_PREFIX="apigw-oidc"


class AwsApigatewayOidcStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        auth0_endpoint = CfnParameter(self, "auth0Endpoint", type="String",
            description="The name of the Amazon S3 bucket where uploaded files will be stored.")

        caller_client_id = CfnParameter(self, "callerClientId", type="String", no_echo=True,
            description="The name of the Amazon S3 bucket where uploaded files will be stored.")

        caller_secret = CfnParameter(self, "callerSecret", type="String", no_echo=True,
            description="The name of the Amazon S3 bucket where uploaded files will be stored.")

        api_audience = CfnParameter(self, "apiAudience", type="String",
            description="The name of the Amazon S3 bucket where uploaded files will be stored.")

        ssm.StringParameter(
            self, 'Auth0EndpointParam',
            parameter_name=f'/{RESOURCE_PREFIX}/auth0_endpoint',
            string_value=auth0_endpoint.value_as_string,
            description='API Gateway mapping table',
            simple_name=False
        )


        lambdaLayer = lambda_.LayerVersion(self, 'lambda-layer',
            code = lambda_.AssetCode('src/oidc-layer/'),
            compatible_runtimes = [lambda_.Runtime.PYTHON_3_9],
        )

        authorizer = lambda_python.PythonFunction(self, f"{RESOURCE_PREFIX}-authorizer-lambda",
                    runtime=lambda_.Runtime.PYTHON_3_9,
                    entry="src/authorizer",
                    index="authorizer.py",
                    handler="lambda_handler",
                    log_retention=logs.RetentionDays.THREE_DAYS,
                    timeout= Duration.seconds(300),
                    layers = [lambdaLayer],
                    )
                    
        backend = lambda_.Function(self, f"{RESOURCE_PREFIX}-backend-lambda",
                    runtime=lambda_.Runtime.PYTHON_3_9,
                    code=lambda_.Code.from_asset("src/api-backend"),
                    handler="api-backend.lambda_handler",
                    log_retention=logs.RetentionDays.THREE_DAYS,
                    timeout= Duration.seconds(300),
                    layers = [lambdaLayer]
                    )

        api = apigateway.RestApi(self, f"{RESOURCE_PREFIX}-api",
                  rest_api_name="{RESOURCE_PREFIX}-api",
                  deploy_options=apigateway.StageOptions(
                    stage_name="dev"
                    )
                )
        
        Tags.of(api).add("audience",api_audience.value_as_string)
                  
        auth = apigateway.TokenAuthorizer(self, f"{RESOURCE_PREFIX}-authorizer",
            handler=authorizer,
            validation_regex="^Bearer [-0-9a-zA-z\\.]*$"
        )

        lambda_integration = apigateway.LambdaIntegration(backend,
                request_templates={"application/json": '{ "statusCode": "200" }'})

        api.root.add_method("GET", lambda_integration, authorizer=auth)   # GET /
        api.root.add_method("POST", lambda_integration, authorizer=auth)   # POST /


        items = api.root.add_resource("items")
        items.add_method("GET", lambda_integration, authorizer=auth) # GET /items
        items.add_method("POST", lambda_integration, authorizer=auth) # POST /items

        caller = lambda_.Function(self, f"{RESOURCE_PREFIX}-caller-lambda",
                    runtime=lambda_.Runtime.PYTHON_3_9,
                    code=lambda_.Code.from_asset("src/caller"),
                    handler="caller.lambda_handler",
                    log_retention=logs.RetentionDays.THREE_DAYS,
                    timeout= Duration.seconds(300),
                    environment=dict(
                        API_URL=api.url,
                        API_ID=api.rest_api_id,
                        REGION=self.region,
                        CLIENT_ID=caller_client_id.value_as_string,
                        CLIENT_SECRET=caller_secret.value_as_string)
                    )

        caller.add_to_role_policy(
            statement=iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ssm:GetParameter"
                ],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/{RESOURCE_PREFIX}/auth0_endpoint"
                ]
            )
        )
        
        caller.add_to_role_policy(
            statement=iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "apigateway:GET"
                ],
                resources=[
                    f"arn:aws:apigateway:{self.region}::/tags/*"
                ]
            )
        )


        # Read the ID of the created API Gateway
        api_id = api.rest_api_id

        # Create an SSM parameter with a JSON template based on the API ID
        mapping_table = {
            "/": {
                "GET": "read:info",
                "POST": "write:info"
            },
            "/items": {
                "GET": "read:items",
                "POST": "write:items"
            }
        }
        ssm.StringParameter(
            self, 'MappingTableParameter',
            parameter_name=f'/{RESOURCE_PREFIX}/{api_id}/mapping_table',
            string_value=json.dumps(mapping_table),
            description='API Gateway mapping table',
            simple_name=False
        )


        authorizer.add_to_role_policy(
            statement=iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ssm:GetParameter"
                ],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/{RESOURCE_PREFIX}/{api_id}/mapping_table"
                ]
            )
        )

        authorizer.add_to_role_policy(
            statement=iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ssm:GetParameter"
                ],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/{RESOURCE_PREFIX}/auth0_endpoint"
                ]
            )
        )
        
        authorizer.add_to_role_policy(
            statement=iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "apigateway:GET"
                ],
                resources=[
                    f"arn:aws:apigateway:{self.region}::/tags/*"
                ]
            )
        )


        backend.add_to_role_policy(
            statement=iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ssm:GetParameter"
                ],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/{RESOURCE_PREFIX}/{api_id}/mapping_table"
                ]
            )
        )

        backend.add_to_role_policy(
            statement=iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ssm:GetParameter"
                ],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/{RESOURCE_PREFIX}/auth0_endpoint"
                ]
            )
        )
        
        backend.add_to_role_policy(
            statement=iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "apigateway:GET"
                ],
                resources=[
                    f"arn:aws:apigateway:{self.region}::/tags/*"
                ]
            )
        )

