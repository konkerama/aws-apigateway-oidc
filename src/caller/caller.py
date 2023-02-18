import http.client
import json
import os
from urllib.parse import urlparse
import boto3

client = boto3.client('apigateway')
ssm = boto3.client('ssm')

RESOURCE_PREFIX ="apigw-oidc"
CLIENT_ID       = os.environ['CLIENT_ID']
CLIENT_SECRET   = os.environ['CLIENT_SECRET']
API_ENDPOINT    = os.environ['API_URL']
API_ID          = os.environ['API_ID']
REGION          = os.environ['REGION']

ENDPOINT=urlparse(API_ENDPOINT).netloc

def get_auth0_domain():
    # Get the mapping table JSON file from AWS Systems Manager Parameter Store
    response = ssm.get_parameter(Name=f"/{RESOURCE_PREFIX}/auth0_endpoint", WithDecryption=False)
    endpoint = response['Parameter']['Value']

    return endpoint

def get_audience(api_id, region):
    response = client.get_tags(resourceArn=f"arn:aws:apigateway:{region}::/restapis/{api_id}")
    return response['tags']['audience']

def generate_token(auth0_domain, audience):
    conn = http.client.HTTPSConnection(auth0_domain)
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'audience': audience,
        'grant_type': 'client_credentials'
    }
    headers = { 'content-type': "application/json" }
    conn.request("POST", "/oauth/token", json.dumps(payload), headers)
    res = conn.getresponse()
    data = res.read()
    response = data.decode("utf-8")
    token = json.loads(response)["access_token"]
    return token

def api_call(endpoint, method, path):
    print (f"calling api endpoint: {method} {endpoint}{path}")
    auth0_domain = get_auth0_domain()
    audience = get_audience(API_ID, REGION)
    token=generate_token(auth0_domain, audience)
    conn = http.client.HTTPSConnection(endpoint)
    headers = { 'authorization': f"Bearer {token}" }
    conn.request(method, path, headers=headers)
    res = conn.getresponse()
    print ("response from api:")
    print (res.read().decode("utf-8"))
    status_code = res.status
    print (f"status code: {status_code}")

def lambda_handler(event,context):
    api_call(ENDPOINT, "GET", "/dev")
    api_call(ENDPOINT, "POST", "/dev")
    api_call(ENDPOINT, "GET", "/dev/items")
    api_call(ENDPOINT, "POST", "/dev/items")
    
if __name__ == "__main__": 
    lambda_handler("","")