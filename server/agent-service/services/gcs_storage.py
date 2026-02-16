"""Google Cloud Storage utility for uploading step images."""
import hashlib
import io
import logging
import os

from PIL import Image
from google.cloud import storage

logger = logging.getLogger(__name__)


class GCSStorage:
    """Upload images to Google Cloud Storage and return public URLs."""

    def __init__(self):
        self.bucket_name = os.getenv("GCS_BUCKET_NAME", "raimy-step-images")
        self._client = None
        self._bucket = None

    @property
    def client(self):
        if self._client is None:
            self._client = storage.Client()
        return self._client

    @property
    def bucket(self):
        if self._bucket is None:
            self._bucket = self.client.bucket(self.bucket_name)
        return self._bucket

    def _optimize_image(self, image_bytes: bytes, quality: int, max_size: int = 512) -> bytes:
        """Optimize image for web: resize if needed, re-encode as JPEG."""
        original_size = len(image_bytes)
        img = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if needed (e.g. PNG with alpha)
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Resize to max_size on longest side if larger
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        optimized_bytes = buf.getvalue()

        logger.info(
            f"GCS: Image optimized {original_size / 1024:.0f}KB -> {len(optimized_bytes) / 1024:.0f}KB "
            f"(quality={quality}, size={img.size[0]}x{img.size[1]})"
        )
        return optimized_bytes

    def upload_image(self, image_bytes: bytes, image_description: str, width: int = 512, height: int = 512, quality: int = 72) -> str:
        """
        Upload image to GCS, return public URL.

        File naming: step-images/{sha256_of_description}_{width}x{height}.jpg
        This ensures the same description always maps to the same filename,
        preventing duplicate uploads.
        """
        text_hash = hashlib.sha256(image_description.lower().strip().encode()).hexdigest()[:16]
        filename = f"step-images/{text_hash}_{width}x{height}.jpg"

        blob = self.bucket.blob(filename)

        # Skip upload if already exists (same description = same hash = same file)
        if blob.exists():
            logger.info(f"GCS: File already exists: {filename}")
            blob.make_public()
            return blob.public_url

        optimized_bytes = self._optimize_image(image_bytes, quality)

        blob.upload_from_string(optimized_bytes, content_type="image/jpeg")
        blob.make_public()

        logger.info(f"GCS: Uploaded {filename} ({len(optimized_bytes)} bytes)")
        return blob.public_url
