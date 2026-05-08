# Phase 3: Image Generation Service (standalone)

## Checklist

- [x] Create `server/image-gen-service/main.py` with FastAPI + FLUX pipeline
- [x] Create `server/image-gen-service/Dockerfile` (CUDA-enabled)
- [x] Create `server/image-gen-service/requirements.txt`
- [ ] Verify `/health` and `/generate` endpoints work locally (requires GPU — test on Windows PC)
- [x] Commit

## New files — `server/image-gen-service/`

```
server/image-gen-service/
  main.py              # FastAPI app -- thin image generator
  Dockerfile           # CUDA-enabled, NOT added to docker-compose
  requirements.txt
```

### `requirements.txt`

```
fastapi==0.115.0
uvicorn==0.30.6
diffusers>=0.30.0
torch>=2.0.0
accelerate>=0.33.0
sentencepiece>=0.2.0
transformers>=4.44.0
Pillow>=10.0.0
```

### `main.py` — Full implementation

```python
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
import time
from contextlib import asynccontextmanager

import torch
from diffusers import FluxPipeline
from fastapi import FastAPI, HTTPException
from PIL import Image
from pydantic import BaseModel

logger = logging.getLogger(__name__)

MODEL_ID = "black-forest-labs/FLUX.1-schnell"  # Swap to FLUX.2 klein 4B when available
pipe: FluxPipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load FLUX model on startup, keep in GPU memory."""
    global pipe
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    logger.info(f"Loading {MODEL_ID} on {device}...")
    pipe = FluxPipeline.from_pretrained(MODEL_ID, torch_dtype=dtype)
    pipe = pipe.to(device)

    # Enable memory optimizations for consumer GPUs
    if device == "cuda":
        pipe.enable_attention_slicing()

    logger.info("Model loaded and ready.")
    yield


app = FastAPI(title="Raimy Image Gen Service", lifespan=lifespan)


class GenerateRequest(BaseModel):
    prompt: str
    width: int = 1024
    height: int = 1024  # 1:1 square (IG-style)
    num_inference_steps: int = 4  # FLUX schnell is fast
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

    seed = request.seed or int(time.time()) % 2**32
    generator = torch.Generator(device=pipe.device).manual_seed(seed)

    start = time.perf_counter()
    result = pipe(
        prompt=request.prompt,
        width=request.width,
        height=request.height,
        num_inference_steps=request.num_inference_steps,
        generator=generator,
    )
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    image: Image.Image = result.images[0]

    # Convert to base64 PNG
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    logger.info(f"Generated image: {request.width}x{request.height}, {elapsed_ms}ms, seed={seed}")

    return GenerateResponse(
        image_base64=image_base64,
        inference_time_ms=elapsed_ms,
        seed=seed,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=False, log_level="info")
```

### `Dockerfile` — CUDA-enabled, for later deployment on GPU machine

```dockerfile
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

EXPOSE 8005

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8005/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
```

**Key design**: NOT added to docker-compose.yml. Run standalone:
- Dev (this Mac): `cd server/image-gen-service && python main.py`
- Production (RTX 3080 Windows PC): `docker build -t raimy-imagegen . && docker run -p 8005:8005 --gpus all raimy-imagegen`

## Verification (local dev on Mac)

- `cd server/image-gen-service && pip install -r requirements.txt && python main.py`
- `curl http://localhost:8005/health` -> shows model + device info
- `curl -X POST http://localhost:8005/generate -H 'Content-Type: application/json' -d '{"prompt":"cooking scene: dicing onions on a wooden cutting board, food photography, warm lighting"}' | python -c "import sys,json,base64; data=json.load(sys.stdin); open('/tmp/test.png','wb').write(base64.b64decode(data['image_base64']))"`
- Open `/tmp/test.png` to verify

---

## Windows Deployment (RTX 3080 PC) — Full Instructions

The image-gen service runs as a Docker container on Windows with GPU passthrough via WSL2. The Dockerfile uses a Linux base image — no Windows-specific code changes needed.

### Prerequisites

**1. Windows version**
- Windows 10 (21H2+) or Windows 11
- Check: `winver` in Run dialog

**2. WSL2**
- Open PowerShell as Administrator:
  ```powershell
  wsl --install
  ```
- Restart if prompted. This installs Ubuntu by default.
- Verify: `wsl --list --verbose` should show Ubuntu with VERSION 2

**3. NVIDIA GPU driver (Windows side)**
- Download and install the latest Game Ready or Studio driver from https://www.nvidia.com/Download/index.aspx
- Pick your GPU (RTX 3080), OS (Windows 10/11), download and install
- Restart after install
- Verify in PowerShell: `nvidia-smi` should show the GPU and driver version
- **Important**: Do NOT install CUDA toolkit on Windows — the driver alone is enough. CUDA runs inside the container.

**4. Docker Desktop**
- Download from https://www.docker.com/products/docker-desktop/
- During install, ensure "Use WSL 2 instead of Hyper-V" is checked
- After install, open Docker Desktop -> Settings -> General -> confirm "Use the WSL 2 based engine" is on
- Settings -> Resources -> WSL Integration -> enable for your Ubuntu distro
- Verify in PowerShell: `docker --version`

**5. NVIDIA Container Toolkit (inside WSL2)**
- Open WSL2 terminal (type `wsl` in PowerShell or open Ubuntu from Start menu):
  ```bash
  # Add NVIDIA package repository
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

  sudo apt-get update
  sudo apt-get install -y nvidia-container-toolkit

  # Configure Docker runtime
  sudo nvidia-ctk runtime configure --runtime=docker

  # Restart Docker Desktop after this step (from Windows taskbar)
  ```

**6. Verify GPU access in Docker**
- In PowerShell:
  ```powershell
  docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
  ```
- Should print the GPU info table (RTX 3080, driver version, CUDA version)
- If this fails, restart Docker Desktop and try again

### Build and Run the Image Gen Service

**1. Get the code onto the Windows PC**

Either clone the repo or just copy the `server/image-gen-service/` folder:
```powershell
# Option A: Clone the full repo
git clone <your-repo-url>
cd raimy\server\image-gen-service

# Option B: Just copy the folder (3 files: main.py, Dockerfile, requirements.txt)
# Copy via USB, scp, or file share
```

**2. Build the Docker image**
```powershell
cd raimy\server\image-gen-service
docker build -t raimy-imagegen .
```
This will take 10-15 minutes on first build (downloads PyTorch + diffusers + model weights).

**3. Run the container**
```powershell
docker run -d --name raimy-imagegen -p 8005:8005 --gpus all --restart unless-stopped raimy-imagegen
```

Flags explained:
- `-d` — detached (runs in background)
- `--name raimy-imagegen` — container name for easy management
- `-p 8005:8005` — expose port 8005 to the network
- `--gpus all` — pass GPU into container
- `--restart unless-stopped` — auto-restart on boot/crash

**4. Wait for model to load**

First startup downloads the FLUX model (~12GB). Check progress:
```powershell
docker logs -f raimy-imagegen
```
Wait until you see "Model loaded and ready." (5-15 min on first run, instant on subsequent starts since Docker caches layers).

**5. Verify it works**
```powershell
# Health check
curl http://localhost:8005/health

# Generate a test image
curl -X POST http://localhost:8005/generate -H "Content-Type: application/json" -d "{\"prompt\":\"cooking scene: dicing onions, food photography\"}" -o response.json
```

**6. Open the firewall port**

So the Mac (running agent-service in Docker) can reach this PC:
```powershell
# PowerShell as Administrator
New-NetFirewallRule -DisplayName "Raimy Image Gen" -Direction Inbound -LocalPort 8005 -Protocol TCP -Action Allow
```

**7. Find the PC's local IP**
```powershell
ipconfig
# Look for "IPv4 Address" under your active adapter (e.g., 192.168.1.100)
```

### Connect from Mac

On the Mac, set the environment variable so agent-service (in Docker) can reach the Windows PC:

**`.env`** (or `docker-compose.yml`):
```
IMAGE_GEN_SERVICE_URL=http://192.168.1.100:8005
```

Replace `192.168.1.100` with the actual Windows PC IP from the previous step.

Verify connectivity from Mac:
```bash
curl http://192.168.1.100:8005/health
```

### Management Commands (on Windows)

```powershell
# View logs
docker logs -f raimy-imagegen

# Stop
docker stop raimy-imagegen

# Start (after stop or reboot)
docker start raimy-imagegen

# Rebuild after code changes
docker stop raimy-imagegen
docker rm raimy-imagegen
docker build -t raimy-imagegen .
docker run -d --name raimy-imagegen -p 8005:8005 --gpus all --restart unless-stopped raimy-imagegen

# Check GPU usage while generating
docker exec raimy-imagegen nvidia-smi
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| `nvidia-smi` fails in Docker | Restart Docker Desktop, ensure NVIDIA driver is latest |
| "could not select device driver" | Reinstall nvidia-container-toolkit in WSL2, restart Docker |
| Model download hangs | Check internet, try `docker build --no-cache` |
| Out of GPU memory | Reduce `num_inference_steps` or image size in request. RTX 3080 (10GB) should handle 1024x1024 fine |
| Port 8005 not reachable from Mac | Check Windows firewall rule, ensure both machines are on same network |
| Container exits immediately | Check `docker logs raimy-imagegen` for error details |

## Commit
```
feat: add standalone image generation service with FLUX pipeline
```
