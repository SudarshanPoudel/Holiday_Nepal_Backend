import boto3
from botocore.exceptions import ClientError
from app.core.config import settings

def init_s3_bucket():
    # Setup client (with optional LocalStack endpoint)
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
        endpoint_url="http://localstack:4566" if settings.USE_LOCAL_STACK else None
    )

    bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"S3 bucket '{bucket_name}' already exists.")
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"Creating S3 bucket '{bucket_name}'...")
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            raise

if __name__ == "__main__":
    init_s3_bucket()
