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
