from app.modules.storage.service import StorageService
from app.utils.image_utils import validate_and_process_image
import asyncio
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings

async def default_profile_seeder():
    service = StorageService()
    image_content = validate_and_process_image(
        file_content= open("seeder/files/default_profile.jpg", "rb").read(),
        resize_to = (500, 500)
    )
    await service.upload_file(
        key=f"user_profile/default.png",
        file_content= image_content,
        content_type="image/webp"
    )

    print("Seeder: Uploaded default profile image successfully.")

if __name__ == "__main__":
    asyncio.run(default_profile_seeder())
