# Phase 5: GCS Storage Utility

## Checklist

- [x] Create `server/agent-service/services/gcs_storage.py`
- [x] Add `google-cloud-storage` to `server/agent-service/requirements.txt`
- [x] Add GCS env vars to `docker-compose.yml` and `.env.example` (done in phase 4 commit)
- [ ] Set up GCS bucket (one-time manual step)
- [ ] Verify image upload and public URL access (requires GCS bucket)
- [x] Commit

## New file — `server/agent-service/services/gcs_storage.py`

Full implementation:

```python
"""Google Cloud Storage utility for uploading step images."""
import hashlib
import logging
import os
from functools import lru_cache

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

    def upload_image(self, image_bytes: bytes, image_description: str, aspect_ratio: str = "1:1") -> str:
        """
        Upload image to GCS, return public URL.

        File naming: step-images/{sha256_of_description}_{aspect_ratio}.png
        This ensures the same description always maps to the same filename,
        preventing duplicate uploads.

        Args:
            image_bytes: PNG image bytes
            image_description: The LLM-generated image description (used for filename hashing)
            aspect_ratio: Aspect ratio string (e.g., "16:9")

        Returns:
            Public URL of the uploaded image
        """
        # Deterministic filename from description
        text_hash = hashlib.sha256(image_description.lower().strip().encode()).hexdigest()[:16]
        ratio_slug = aspect_ratio.replace(":", "x")
        filename = f"step-images/{text_hash}_{ratio_slug}.png"

        blob = self.bucket.blob(filename)

        # Skip upload if already exists (same description = same hash = same file)
        if blob.exists():
            logger.info(f"GCS: File already exists: {filename}")
            blob.make_public()
            return blob.public_url

        blob.upload_from_string(image_bytes, content_type="image/png")
        blob.make_public()

        logger.info(f"GCS: Uploaded {filename} ({len(image_bytes)} bytes)")
        return blob.public_url
```

**Note**: `upload_from_string` is synchronous (google-cloud-storage doesn't have async). Since image uploads are small (~100-200KB) and this runs in a background task, blocking briefly is acceptable. If needed later, wrap in `asyncio.to_thread()`.

## Dependencies

**`server/agent-service/requirements.txt`** — add: `google-cloud-storage`

## Environment changes

**`docker-compose.yml`** — add to `agent-service` environment (around line 121):
```yaml
- GCS_BUCKET_NAME=${GCS_BUCKET_NAME:-raimy-step-images}
- GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-credentials.json
```

And add a volume mount for the credentials file:
```yaml
volumes:
  - ./server:/app/server
  - ./gcp-credentials.json:/app/gcp-credentials.json:ro  # GCS service account
```

**`.env.example`** — add:
```
GCS_BUCKET_NAME=raimy-step-images     # GCS bucket for step images
```

## GCS Setup (one-time, manual)

1. `gcloud storage buckets create gs://raimy-step-images --location=us-central1`
2. Create service account: `gcloud iam service-accounts create raimy-storage --display-name="Raimy Storage"`
3. Grant permission: `gcloud projects add-iam-policy-binding PROJECT_ID --member="serviceAccount:raimy-storage@PROJECT_ID.iam.gserviceaccount.com" --role="roles/storage.objectAdmin"`
4. Download key: `gcloud iam service-accounts keys create gcp-credentials.json --iam-account=raimy-storage@PROJECT_ID.iam.gserviceaccount.com`
5. Place `gcp-credentials.json` in project root (add to `.gitignore`)

## Verification

- Run a quick upload test from Python
- Verify the returned URL is publicly accessible in a browser

## Commit
```
feat: add GCS storage utility for step image uploads
```
