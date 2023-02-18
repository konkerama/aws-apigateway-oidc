
# Welcome to your CDK Python project!

This solution performs a poc of Open ID Connect in AWS API Gateway. It creates 1 api gateway, 3 Lambda Functions (caller, backend and authorizer) and a shared Lambda layer for storing the required library to verify the jwt token.

## Install CDK
to install cdk locally for this project do: 
```
npm install cdk@latest
```
and to run it:
```
npx aws-cdk deploy
```

## Configure Python 
To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```


## Configure Auth0
First you need to configure an auth0 endpoint by creating 2 application and an api. 
After you have performed that you should be ready to modify the `deploy.sh` script by providing the following info, which all of them can be retrieved from auth0:

* auth0Endpoint: The endpoint of your auth0 environment (eg dev-xxx.us.auth0.com)
* callerClientId: The clientid of your caller application
* callerSecret: The secret of your caller application
* apiAudience: The required audience of your api.

The definition of the apigateway resources, methods and their mapping to the equivalent scope is defined in the `aws_apigateway_oidc_stack.py` file alongside the other infra config.

To test the solution trigger the caller Lambda function, which will generate the oidc token and call the AWS API Gateway.

Based on the scope permissions you have assigned to your application in auth0 the api calls that the caller function performs will be allowed or denied.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation
