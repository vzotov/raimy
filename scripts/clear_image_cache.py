"""Clear image cache: delete GCS blobs, truncate cache table, remove image_url from all recipe steps."""
import os
import psycopg2
from google.cloud import storage

db_url = os.getenv("DATABASE_URL", "postgresql://raimy:raimy@localhost:5432/raimy")
bucket_name = os.getenv("GCS_BUCKET_NAME", "raimy-step-images")
prefix = "step-images/"

# --- GCS cleanup ---
print(f"Deleting all blobs in gs://{bucket_name}/{prefix} ...")
client = storage.Client()
bucket = client.bucket(bucket_name)
blobs = list(bucket.list_blobs(prefix=prefix))
if blobs:
    bucket.delete_blobs(blobs)
    print(f"Deleted {len(blobs)} blobs from GCS.")
else:
    print("No blobs found in GCS.")

# --- DB cleanup ---
conn = psycopg2.connect(db_url)
conn.autocommit = True
with conn.cursor() as cur:
    # 1. Truncate image cache table
    cur.execute("TRUNCATE step_image_cache")
    print("Truncated step_image_cache table.")

    # 2. Remove image_url from all recipe steps in chat_sessions
    cur.execute("""
        UPDATE chat_sessions
        SET recipe = jsonb_set(
            recipe,
            '{steps}',
            (
                SELECT COALESCE(jsonb_agg(step - 'image_url' ORDER BY idx), '[]'::jsonb)
                FROM jsonb_array_elements(recipe->'steps') WITH ORDINALITY AS t(step, idx)
            )
        )
        WHERE recipe->'steps' IS NOT NULL
          AND jsonb_typeof(recipe->'steps') = 'array'
          AND EXISTS (
              SELECT 1 FROM jsonb_array_elements(recipe->'steps') AS s
              WHERE s ? 'image_url'
          )
    """)
    print(f"Cleared image_url from recipe steps in {cur.rowcount} sessions.")

conn.close()
print("Done. All image data cleared.")
