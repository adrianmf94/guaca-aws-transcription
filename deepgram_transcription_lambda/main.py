import boto3
import json
import os
import requests


def generate_presigned_url(bucket_name, object_key, expiration=8500):
    """
    Generate a presigned URL for accessing an S3 object.

    :param bucket_name: The name of the S3 bucket.
    :param object_key: The key of the object in the bucket.
    :param expiration: The duration in seconds for which the presigned URL will be valid. (Default: 3600 seconds)
    :return: The presigned URL as a string.
    """
    s3_client = boto3.client('s3')
    
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=expiration
        )
        return response
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        return None


def handler(event, context):
    
    s3_event = event.get('Records', [])[0].get('s3', {})
    bucket_name = s3_event.get('bucket', {}).get('name')
    object_key = s3_event.get('object', {}).get('key')
    
    try:
        
        presigned_url = generate_presigned_url(bucket_name, object_key)

        if presigned_url:
            print("Presigned URL:", presigned_url)
        else:
            print("Failed to generate presigned URL.")

        DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
        LANGUAGE_OPTION = "es-419"

        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "application/json",
        }

        url=f"https://api.deepgram.com/v1/listen?language={LANGUAGE_OPTION}&punctuate=true&model=nova"

        payload = {
            "url": presigned_url,
        }
        
        print(f"url presigned_url {presigned_url}")

        response = requests.post(
            url=url, 
            headers=headers,
            json=payload,
        )

        print(f"Response code {response.status_code}")
        print(f"Response text {response.text}")

        if response.status_code == 200:
            return {
                "statusCode": 200,
                "body": response.json(),
            }
        else:
            return {
                "statusCode": response.status_code,
                "body": response.text,
            }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }
