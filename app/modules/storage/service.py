import time
import uuid
from botocore.exceptions import ClientError
from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool
import logging
from app.core.config import settings
import boto3
import os
class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url='http://localstack:4566' if settings.USE_LOCAL_STACK else None,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self.use_localstack = settings.USE_LOCAL_STACK

    async def upload_file(self, key: str, file_content: bytes, content_type: str = "application/octet-stream"):
        try:
            await run_in_threadpool(
                self.s3_client.put_object,
                Bucket=self.bucket_name,
                Key=key,
                Body=file_content,
                ContentType=content_type,
            )
            return key
        except ClientError as e:
            logging.error(f"Failed to upload file: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload file to S3")

    def get_file_url(self, key: str) -> str:
        if self.use_localstack:
            return f"http://localhost:4566/{self.bucket_name}/{key}"
        return f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
    
    
    def file_exists(self, key: str) -> bool:
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logging.error(f"Error checking if file exists: {e}")
            raise HTTPException(status_code=500, detail="Failed to check file existence")



    async def delete_file(self, key: str):
        try:
            await run_in_threadpool(
                self.s3_client.delete_object,
                Bucket=self.bucket_name,
                Key=key,
            )
            return {"message": "File deleted successfully", "key": key}
        except ClientError as e:
            logging.error(f"Failed to delete file: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete file from S3")
   
    async def copy_file(self, from_key: str, to_key: str):
        copy_source = {
            'Bucket': self.bucket_name,
            'Key': from_key
        }
        if self.file_exists(from_key):
            await run_in_threadpool(
                self.s3_client.copy_object,
                Bucket=self.bucket_name,
                CopySource=copy_source,
                Key=to_key
            )
            return to_key
        else:
            raise HTTPException(status_code=404, detail="File not found")
        
    def generate_presigned_url(self,key: str, expiration: int = 3600):
        try:
            #to use it with sqlalchemy no need for await
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expiration,
            )
            return {"url": url}
        except ClientError as e:
            logging.error(f"Failed to generate presigned URL: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate presigned URL")

    async def download_from_s3(self, key: str, folder_path: str) -> str | None:
        try:
            response = await run_in_threadpool(
                self.s3_client.get_object,
                Bucket=self.bucket_name,
                Key=key
            )
            body = response["Body"].read()

            os.makedirs(folder_path, exist_ok=True)

            filename = os.path.basename(key)
            full_path = os.path.join(folder_path, filename)

            with open(full_path, "wb") as f:
                f.write(body)

            return full_path
        except ClientError as e:
            logging.error(f"Failed to download file from S3: {e}")
            return None

    def get_file_upload_time(self, key: str):
        """Retrieve the LastModified time of an S3 object."""
        try:
                response = self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
                last_modified = response["LastModified"]  # This is a datetime object
                return last_modified.strftime("%Y-%m-%d %H:%M:%S")  # Format as string
        except Exception as e:
            print(f"Error fetching upload time: {e}")
            return None

    @staticmethod
    def generate_unique_key(file_extension: str = ".bin") -> str:
        unique_id = f"{uuid.uuid4()}_{int(time.time() * 1000)}"
        return f"{unique_id}.{file_extension}"