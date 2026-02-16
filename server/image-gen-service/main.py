"""
Standalone image generation server using FLUX.

Thin FastAPI server: receives prompt, returns base64 image.
No auth, no DB, no storage — just image generation.

Run locally for dev: python main.py
Later deploy on RTX 3080 PC and point IMAGE_GEN_SERVICE_URL to its IP.
"""
import base64
import io
import logging
import random
import time
from contextlib import asynccontextmanager

import torch
from diffusers import Flux2KleinPipeline
from fastapi import FastAPI, HTTPException
from PIL import Image
from pydantic import BaseModel

logger = logging.getLogger(__name__)

MODEL_ID = "black-forest-labs/FLUX.2-klein-4B"
pipe: Flux2KleinPipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load FLUX model on startup, keep in GPU memory."""
    global pipe
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32

    logger.info(f"Loading {MODEL_ID} on {device}...")
    pipe = Flux2KleinPipeline.from_pretrained(MODEL_ID, torch_dtype=dtype)

    if device == "cuda":
        pipe.enable_model_cpu_offload()
    else:
        pipe = pipe.to(device)

    logger.info("Model loaded and ready.")
    yield


app = FastAPI(title="Raimy Image Gen Service", lifespan=lifespan)


class GenerateRequest(BaseModel):
    prompt: str
    width: int = 1024
    height: int = 1024  # 1:1 square (IG-style)
    num_inference_steps: int = 4
    seed: int | None = None


class GenerateResponse(BaseModel):
    image_base64: str
    inference_time_ms: int
    seed: int


@app.get("/health")
async def health():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return {
        "status": "healthy" if pipe else "loading",
        "model": MODEL_ID,
        "device": device,
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate an image from a text prompt. Returns base64-encoded PNG."""
    if not pipe:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    seed = request.seed if request.seed is not None else random.randint(0, 2**32 - 1)
    generator = torch.Generator(device=pipe.device).manual_seed(seed)

    start = time.perf_counter()
    result = pipe(
        prompt=request.prompt,
        width=request.width,
        height=request.height,
        num_inference_steps=request.num_inference_steps,
        guidance_scale=1.0,
        generator=generator,
    )
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    image: Image.Image = result.images[0]

    # Convert to base64 JPEG
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    logger.info(f"Generated image: {elapsed_ms}ms, {request.width}x{request.height}, prompt='{request.prompt[:100]}...'")

    return GenerateResponse(
        image_base64=image_base64,
        inference_time_ms=elapsed_ms,
        seed=seed,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=False, log_level="info")
