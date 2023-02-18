#!/bin/bash

# Download dependencies for Lambda Layer
cd src/oidc-layer/python || exit
pip install -r requirements.txt -t ./lib/python3.9/site-packages --upgrade
cd ../../..

npx aws-cdk deploy --parameters auth0Endpoint=<Auth0Endpoint> \
                   --parameters callerClientId=<CallerApplicationClientId> \
                   --parameters callerSecret=<CallerApplicationSecret> \
                   --parameters apiAudience=<Auth0APIAudience>