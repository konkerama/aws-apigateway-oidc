# pylint: disable=import-error
# type: ignore
import logging
import json
from six.moves.urllib.request import urlopen
from jose import jwt
import boto3


logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client('apigateway')
ssm = boto3.client('ssm')

ALGORITHMS = ["RS256"]

def get_audience(api_id, region):
    response = client.get_tags(resourceArn=f"arn:aws:apigateway:{region}::/restapis/{api_id}")
    logger.info ("required audience: %s", response['tags']['audience'])
    return response['tags']['audience']

def get_auth0_domain(resource_prefix):
    # Get the mapping table JSON file from AWS Systems Manager Parameter Store
    response = ssm.get_parameter(Name=f"/{resource_prefix}/auth0_endpoint",
                                WithDecryption=False)
    endpoint = response['Parameter']['Value']
    logger.info ("auth0 endpoint: %s", endpoint)
    return endpoint

def get_mapping_table_from_ssm(resource_prefix, api_id):
    # Get the mapping table JSON file from AWS Systems Manager Parameter Store
    response = ssm.get_parameter(Name=f"/{resource_prefix}/{api_id}/mapping_table",
                                WithDecryption=False)
    mapping_table_json = response['Parameter']['Value']

    # Parse the mapping table JSON into a Python dictionary
    mapping_table = json.loads(mapping_table_json)
    logger.info ("scope mapping table: %s", mapping_table)
    return mapping_table

def verify_aud(resource_prefix, token, api_id, region):
    auth0_domain = get_auth0_domain(resource_prefix)
    audience = get_audience(api_id, region)
    # token = get_token_auth_header()
    try:
        jsonurl = urlopen("https://"+auth0_domain+"/.well-known/jwks.json")
        jwks = json.loads(jsonurl.read())
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
        if rsa_key:
            try:
                logger.info ("decoding token")
                jwt.decode(
                    token,
                    rsa_key,
                    algorithms=ALGORITHMS,
                    audience=audience,
                    issuer="https://"+auth0_domain+"/"
                )
            except jwt.ExpiredSignatureError:
                logger.error ("token_expired")
                return False
            except jwt.JWTClaimsError:
                logger.error ("invalid_claims: please check the audience and issuer")
                return False
            except Exception as e:
                logger.error ("invalid_header: Unable to parse authentication token.")
                logger.error (e)
                return False
            logger.error ("token decode ok")
            return True

    except Exception as e:
        logger.error ("invalid_header: Unable to parse authentication token.")
        logger.error (e)
        return False

def get_scope(api_id, resource, http_method, resource_prefix):
    mapping_table = get_mapping_table_from_ssm(resource_prefix, api_id)
    scope = mapping_table.get(resource, {}).get(http_method)
    logger.info ("required scope: %s", scope)
    return scope

def verify_scope(token, api_id, resource, http_method, resource_prefix):
    """Determines if the required scope is present in the Access Token
    Args:
        required_scope (str): The scope required to access the resource
    """
    required_scope = get_scope (api_id, resource, http_method, resource_prefix)

    unverified_claims = jwt.get_unverified_claims(token)
    if unverified_claims.get("scope"):
        token_scopes = unverified_claims["scope"].split()
        logger.info ("token_scopes: %s", token_scopes)
        for token_scope in token_scopes:
            if token_scope == required_scope:
                logger.info ("scope authorized")
                return True
    logger.error ("scope not authorized")
    return False

def verify_authorization(token, api_id, resource, http_method, resource_prefix, region):
    if verify_aud(resource_prefix, token, api_id, region):
        return verify_scope(token, api_id, resource, http_method, resource_prefix)
    return False
