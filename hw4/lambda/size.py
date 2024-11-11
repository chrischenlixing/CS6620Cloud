import boto3
from datetime import datetime
import os
import json

# Initialize clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['DYNAMODB_TABLE_NAME']

def calculate_bucket_size(bucket_name):
    # Get the list of objects in the bucket
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    total_size = 0
    object_count = 0
    
    if 'Contents' in response:
        # Calculate the total size and count the objects
        for obj in response['Contents']:
            total_size += obj['Size']
            object_count += 1
    
    return total_size, object_count

def write_size_to_dynamodb(bucket_name, total_size, object_count):
    table = dynamodb.Table(table_name)
    timestamp = int(datetime.utcnow().timestamp())
    timestamp_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    # Write data to DynamoDB
    table.put_item(
        Item={
            'BucketName': bucket_name,
            'Timestamp': timestamp,
            'TimestampStr': timestamp_str,
            'TotalSize': total_size,
            'ObjectCount': object_count
        }
    )

def lambda_handler(event, context):
    # Loop through each record in the SQS event
    for record in event['Records']:
        # Parse the SQS message body as JSON
        message = json.loads(record['body'])
        
        # Extract the S3 bucket and object key information from the SNS message
        sns_message = json.loads(message['Message'])
        for s3_event in sns_message['Records']:
            bucket_name = s3_event['s3']['bucket']['name']

            # Calculate the total size and object count of the bucket
            total_size, object_count = calculate_bucket_size(bucket_name)

            # Write the data to DynamoDB
            write_size_to_dynamodb(bucket_name, total_size, object_count)

    return {
        'statusCode': 200,
        'body': 'Size tracking Lambda executed successfully for all records.'
    }
