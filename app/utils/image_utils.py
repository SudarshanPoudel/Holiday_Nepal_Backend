from PIL import Image
from io import BytesIO

ALLOWED_IMAGE_TYPES = {"JPEG", "PNG", "JPG", "WEBP"}

def validate_and_process_image(
    file_content: bytes,
    max_size_mb: float = 5.0,
    resize_to: tuple[int | None, int | None] | None = None,  # (width, height)
    target_format: str = "WEBP",
) -> bytes:
    size_mb = len(file_content) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ValueError(f"Image exceeds max size of {max_size_mb}MB")

    try:
        with Image.open(BytesIO(file_content)) as img:
            if img.format.upper() not in ALLOWED_IMAGE_TYPES:
                raise ValueError(f"Unsupported image format: {img.format}")

            if img.mode in ("RGBA", "P", "LA", "CMYK"):
                img = img.convert("RGB")

            if resize_to:
                width, height = resize_to

                if width and height:
                    # Both dimensions given -> stretch
                    img = img.resize((width, height))
                elif width:
                    # Resize width, keep aspect ratio
                    w_percent = width / float(img.width)
                    h_size = int(float(img.height) * w_percent)
                    img = img.resize((width, h_size))
                elif height:
                    # Resize height, keep aspect ratio
                    h_percent = height / float(img.height)
                    w_size = int(float(img.width) * h_percent)
                    img = img.resize((w_size, height))
                # else: both None, no resize

            output_buffer = BytesIO()
            img.save(output_buffer, format=target_format.upper(), quality=85)
            return output_buffer.getvalue()

    except Exception as e:
        raise ValueError(f"Invalid image file: {e}")
