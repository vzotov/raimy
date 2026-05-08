# Phase 2: Embedding Service

## Checklist

- [x] Create `server/embedding-service/main.py` with FastAPI + sentence-transformers
- [x] Create `server/embedding-service/Dockerfile`
- [x] Create `server/embedding-service/requirements.txt`
- [x] Add embedding-service to `docker-compose.yml`
- [x] Verify `/health` and `/embed` endpoints work
- [ ] Commit

## New files — `server/embedding-service/`

```
server/embedding-service/
  main.py              # FastAPI app
  Dockerfile
  requirements.txt
```

### `requirements.txt`

```
fastapi==0.115.0
uvicorn==0.30.6
sentence-transformers==3.0.1
torch>=2.0.0
pydantic>=2.0.0
```

### `main.py` — Full implementation

```python
"""Embedding service for step image caching. Converts text to 384-dim vectors."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
model: SentenceTransformer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup."""
    global model
    logger.info(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    logger.info(f"Model loaded. Embedding dimension: {model.get_sentence_embedding_dimension()}")
    yield


app = FastAPI(title="Raimy Embedding Service", lifespan=lifespan)


class EmbedRequest(BaseModel):
    texts: list[str]


class EmbedResponse(BaseModel):
    embeddings: list[list[float]]


@app.get("/health")
async def health():
    return {
        "status": "healthy" if model else "loading",
        "model": MODEL_NAME,
        "dimension": 384,
    }


@app.post("/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest):
    """Generate embeddings for a list of texts.

    Receives image_description strings (already LLM-normalized).
    Only does basic cleanup: lowercase, strip whitespace.
    """
    cleaned = [t.lower().strip() for t in request.texts]
    embeddings = model.encode(cleaned).tolist()
    return EmbedResponse(embeddings=embeddings)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True)
```

### `Dockerfile` — Follow the pattern from `server/auth-service/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

ENV PYTHONPATH=/app

EXPOSE 8004

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
```

Note: `start_period=60s` because the sentence-transformers model download on first run takes time.

### Add to `docker-compose.yml` — insert before the `volumes:` section at the bottom

```yaml
  embedding-service:
    build: ./server/embedding-service
    ports:
      - "8004:8004"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

## Verification

- `docker compose up -d --build embedding-service`
- Wait for healthcheck: `docker compose ps` should show "healthy"
- `curl -s http://localhost:8004/health` -> `{"status":"healthy","model":"...","dimension":384}`
- `curl -s -X POST http://localhost:8004/embed -H 'Content-Type: application/json' -d '{"texts":["dicing onions finely on a cutting board"]}'` -> returns JSON with one 384-element array

## Commit
```
feat: add embedding service for step image similarity search
```
