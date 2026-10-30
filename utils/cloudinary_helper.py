import cloudinary
import cloudinary.uploader
import os
from fastapi import HTTPException, UploadFile, status

# Configure Cloudinary credentials
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "your_cloud_name"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "your_api_key"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", "your_api_secret"),
    secure=True
)

async def upload_image_to_cloudinary(file: UploadFile) -> str:
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed."
        )
    try:
        contents = await file.read()
        response = cloudinary.uploader.upload(
            contents,
            folder="logjournal/profiles",
            resource_type="image"
        )
        return response.get("secure_url")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image to Cloudinary: {str(e)}"
        )