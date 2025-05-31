import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
import logging

AWS_STORAGE_BUCKET_NAME = settings.AWS_STORAGE_BUCKET_NAME
AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
AWS_REGION = settings.AWS_REGION
LOCALSTACK_ENDPOINT = "http://localstack:4566" if settings.USE_LOCAL_STACK else None

def create_bucket_if_not_exists(
    bucket_name: str = AWS_STORAGE_BUCKET_NAME,
    endpoint_url: str = LOCALSTACK_ENDPOINT,
    aws_access_key_id: str = AWS_ACCESS_KEY_ID,
    aws_secret_access_key: str = AWS_SECRET_ACCESS_KEY,
    region_name: str = AWS_REGION,
) -> None:
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name,
    )

    try:
        s3.head_bucket(Bucket=bucket_name)
        logging.info(f'Bucket "{bucket_name}" already exists.')
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            s3.create_bucket(Bucket=bucket_name)
            logging.info(f'Bucket "{bucket_name}" created.')
        else:
            logging.error(f"Error checking/creating bucket: {e}")
            raise