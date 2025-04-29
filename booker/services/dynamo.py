import logging
import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_all_users(table_name=None):
    if not table_name:
        table_name = os.environ['USERS_TABLE_NAME']

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    try:
        response = table.scan()
        return response.get('Items', [])
    except ClientError as e:
        logger.error(f"Error scanning table: {e.response['Error']['Message']}")
        return []


def get_user(user_id, table_name=None):
    if not table_name:
        table_name = os.environ['USERS_TABLE_NAME']

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    try:
        response = table.get_item(Key={'userId': user_id})
        return response.get('Item')
    except ClientError as e:
        logger.error(
            f"Error retrieving user: {e.response['Error']['Message']}")
        return None


def store_booking_result(user_id, booking_date, status, details=None):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['USERS_TABLE_NAME'])

    result = {
        'date': booking_date.isoformat(),
        'status': status,
        'timestamp': datetime.now().isoformat()
    }

    if details:
        result.update(details)

    try:
        table.update_item(
            Key={'userId': user_id},
            UpdateExpression="SET bookingResults = list_append(if_not_exists(bookingResults, :empty_list), :result)",
            ExpressionAttributeValues={
                ':empty_list': [],
                ':result': [result]
            },
            ReturnValues="UPDATED_NEW"
        )
        return True
    except ClientError as e:
        logger.error(f"Error storing result: {e.response['Error']['Message']}")
        return False
