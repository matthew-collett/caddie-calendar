import boto3
import json


def get_secret(secret_id):
    secretsmanager = boto3.client('secretsmanager')
    response = secretsmanager.get_secret_value(
        SecretId=secret_id
    )
    return response['SecretString'].encode()
