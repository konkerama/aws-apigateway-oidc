# pylint: disable=import-error
# type: ignore
from oidc_layer import verify_authorization
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

RESOURCE_PREFIX="apigw-oidc"
ALGORITHMS = ["RS256"]

def get_api_info(arn):
    # format is arn:aws:execute-api:<region>:<aws-account>:<api-id>/ESTestInvoke-stage/GET/
    api_arn_components = arn.split(':')
    api_region = api_arn_components[3]
    
    path_arn_components = api_arn_components[5].split('/')
    api_id = path_arn_components[0]
    resource = '/' + '/'.join(path_arn_components[3:])
    http_method = path_arn_components[2]

    return api_id, api_region, resource, http_method

def generate_policy(effect, resource):
    return {
        'policyDocument':{
            'Version': '2012-10-17',
            'Statement': [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": resource
                }
            ]
        }
    }
    
def lambda_handler(event, context):
    logger.info(context)
    logger.info(event)

    token= event['authorizationToken'].split()[1]

    api_id, api_region, resource, http_method = get_api_info(event['methodArn'])

    logger.info(f"api id: {api_id}")
    logger.info(f"api region: {api_region}")
    logger.info(f"resource: {resource}")
    logger.info(f"http_method: {http_method}")

    if verify_authorization(token, api_id, resource, http_method, RESOURCE_PREFIX, api_region):
        return generate_policy("allow",event['methodArn'])
    else:
        return generate_policy("deny",event['methodArn'])

    

