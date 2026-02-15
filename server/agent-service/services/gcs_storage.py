"""Google Cloud Storage utility for uploading step images."""
import hashlib
import logging
import os

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

    def upload_image(self, image_bytes: bytes, image_description: str, width: int = 512, height: int = 512) -> str:
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

        blob.upload_from_string(image_bytes, content_type="image/jpeg")
        blob.make_public()

        logger.info(f"GCS: Uploaded {filename} ({len(image_bytes)} bytes)")
        return blob.public_url
