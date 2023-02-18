import aws_cdk as core
import aws_cdk.assertions as assertions

from aws_apigateway_oidc.aws_apigateway_oidc_stack import AwsApigatewayOidcStack

# example tests. To run these tests, uncomment this file along with the example
# resource in aws_apigateway_oidc/aws_apigateway_oidc_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AwsApigatewayOidcStack(app, "aws-apigateway-oidc")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
