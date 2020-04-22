#!/usr/bin/python
import boto3


def create_user(username, password, user_pool_id, app_client_id, email):
    client = boto3.client("cognito-idp")

    try:
        # initial sign up
        resp = client.sign_up(
            ClientId=app_client_id,
            Username=username,
            Password=password,
            UserAttributes=[{"Name": "email", "Value": email}],
        )
        # then confirm signup
        resp = client.admin_confirm_sign_up(UserPoolId=user_pool_id, Username=username)
        print(f"[INFO] {resp}")
        return True
    except Exception as e:
        raise e


def authenticate_and_get_token(username, password, user_pool_id, app_client_id):
    client = boto3.client("cognito-idp")
    try:
        resp = client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=app_client_id,
            AuthFlow="ADMIN_NO_SRP_AUTH",
            AuthParameters={"USERNAME": username, "PASSWORD": password},
        )
        print(f"INFO: {resp['AuthenticationResult']}")

        return resp["AuthenticationResult"]
    except Exception as e:
        raise e
