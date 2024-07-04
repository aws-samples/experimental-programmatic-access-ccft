import boto3
import os

def lambda_handler(event, context):

    s3_bucket = os.environ['bucketName']
        
    # Create an S3 client
    s3 = boto3.client('s3')
    
    # Retrieve the list of objects in the bucket
    response = s3.list_objects_v2(Bucket=s3_bucket)
    
    # Check if the bucket is empty
    if 'Contents' in response:
        is_empty = False
    else:
        is_empty = True

    return {
        'statusCode': 200,
        'isEmpty': is_empty
    }
