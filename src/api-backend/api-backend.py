# pylint: disable=import-error
# type: ignore
from oidc_layer import verify_authorization
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

RESOURCE_PREFIX="apigw-oidc"


def lambda_handler(event, context):

    token= event['headers']['Authorization'].split()[1]
    api_id = event['requestContext']['apiId']
    api_region=event['requestContext']['domainName'].split('.')[2]
    resource=event['resource']
    http_method=event['httpMethod']

    logger.info(f"api id: {api_id}")
    logger.info(f"api region: {api_region}")
    logger.info(f"resource: {resource}")
    logger.info(f"http_method: {http_method}")

    response = {
      "statusCode": 200,
      "headers": {
        "Content-Type": "application/json"
      },
      "isBase64Encoded": False,
      "multiValueHeaders": { 
        "X-Custom-Header": ["My value", "My other value"],
      },
      "body": "{\n  \"message\": \"Hello from Lambda\" \n}"
    }

    if verify_authorization(token, api_id, resource, http_method, RESOURCE_PREFIX, api_region):
        return response
    return "denied"