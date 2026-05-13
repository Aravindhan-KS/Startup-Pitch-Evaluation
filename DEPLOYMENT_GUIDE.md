# Colab + ngrok Deployment Guide

## Overview

This guide explains how to run the Startup Pitch Evaluation backend on Google Colab with a GPU runtime and expose it through ngrok.

The goal is simple: use the same backend pipeline you run locally, but start it inside Colab so you can use GPU-backed inference without deploying to a hosted service.

---

## 1. What You Need

- A Google account for Colab.
- A GPU runtime in Colab, preferably T4.
- An ngrok auth token from https://dashboard.ngrok.com/auth/your-authtoken.
- This repository uploaded or cloned inside Colab.

---

## 2. How the Setup Works

1. Colab installs the Python and system dependencies.
2. Colab mounts or clones the repo.
3. The notebook verifies the GPU and model files.
4. A FastAPI server starts on port 8000.
5. ngrok creates a public HTTPS tunnel to that port.
6. You use the public URL for `/health`, `/evaluate`, and `/docs`.

---

## 3. Step-by-Step Setup

### Step 1: Open the notebook

Open [colab_deployment.ipynb](colab_deployment.ipynb) in Colab.

### Step 2: Switch runtime to GPU

In Colab, choose Runtime -> Change runtime type -> GPU.

### Step 3: Run the setup cells

Run the notebook cells in order:

1. GPU and system info check
2. System dependency install
3. Python dependency install
4. Repository preparation
5. ngrok token configuration
6. Model checkpoint verification
7. FastAPI server start and ngrok tunnel creation
8. Health check and evaluation tests

### Step 4: Copy the public URL

The notebook prints a URL like:

```text
https://xxxx-xxxx.ngrok-free.app
```

Use that URL for the API and UI.

---

## 4. What Each Cell Does

### Cell 1

Confirms GPU access and checks for ffmpeg.

### Cell 2

Installs ffmpeg and image libraries needed for audio/video processing.

### Cell 3

Installs FastAPI, PyTorch, whisper, ngrok, and related packages.

### Cell 4

Prepares the repository path used by the backend.

### Cell 5

Registers your ngrok auth token.

### Cell 6

Checks that the model checkpoint exists.

### Cell 7

Starts Uvicorn and creates the ngrok tunnel.

### Cell 8

Checks `/health`.

### Cell 9

Sends a sample evaluation request.

### Cell 10

Prints the final public URL and usage notes.

### Cell 11

Keeps the API alive while the notebook stays open.

### Cell 12

Stops the API if you want to shut it down.

---

## 5. Data Processing Flow

The backend still processes data the same way as it does locally:

1. Preprocessing splits the pitch into 5-second chunks.
2. Video extraction samples frames and visual metadata.
3. Audio extraction creates WAV chunks and audio quality signals.
4. Feature extraction computes text, visual, and audio scores.
5. Fusion combines the modalities.
6. Scoring produces the final evaluation report.

Because Colab can run on GPU, the neural path can be used when the checkpoint and dependencies are available.

---

## 6. Testing the Live API

Once the tunnel is up:

### Health check

```bash
curl https://YOUR_NGROK_URL/health
```

### API docs

```text
https://YOUR_NGROK_URL/docs
```

### Evaluate a pitch payload

```bash
curl -X POST "https://YOUR_NGROK_URL/evaluate" \
  -H "Content-Type: application/json" \
  -d '{"title":"Sample Pitch","transcript":"We solve X problem","language_hint":"en"}'
```

### Upload a video

Use the `/evaluate/upload` endpoint from the browser UI or a form client.

---

## 7. Important Limits

- Colab free sessions are temporary.
- ngrok URLs can change when the session restarts.
- Keep the notebook running if you want the API to stay live.
- Large or long videos may still be slow even with GPU.

---

## 8. Troubleshooting

### GPU not visible

Switch Colab runtime to GPU and rerun the notebook.

### ngrok tunnel fails

Re-run the token cell and confirm the token is valid.

### Checkpoint missing

Make sure the repo content inside Colab includes `backend/models/checkpoints/phase6_gpu_nn_model.pt`.

### Health check fails right after startup

Wait a few seconds and retry. The model may still be loading.

---

## 9. Quick Summary

1. Open [colab_deployment.ipynb](colab_deployment.ipynb).
2. Switch Colab to GPU.
3. Set your ngrok token.
4. Run the notebook cells in order.
5. Use the printed ngrok URL to access the live API.

---

## 10. Alternative: Local Backend + Streamlit Frontend

### Local Backend Deployment

For development or self-hosted deployments, see [DEPLOY_BACKEND.md](DEPLOY_BACKEND.md) for:

- Running FastAPI locally with uvicorn
- Exposing via ngrok (public tunnel)
- Docker containerization
- Self-hosted custom domains with nginx + TLS
- Render.com or similar platform deployments

Quick start:

```bash
# Activate environment
.venv\Scripts\Activate.ps1  # Windows

# Run backend on localhost:8000
.\run_backend.ps1
```

Or with custom configuration:

```bash
$env:USE_HEURISTIC_PIPELINE = 'true'  # Use fast heuristic (no GPU needed)
$env:PORT = '8000'
.\run_backend.ps1
```

### Streamlit Frontend

Deploy the frontend as a Streamlit app:

```bash
# Install Streamlit dependencies
pip install -r requirements-streamlit.txt

# Set backend API URL
$env:STREAMLIT_API_URL = 'http://localhost:8000'

# Run Streamlit
streamlit run streamlit_app.py
```

The Streamlit wrapper:

- Automatically inlines your frontend assets (HTML, CSS, JS)
- Prefers `backend/app/static` by default
- Injects a JS shim to route all API calls to the configured backend
- Supports both local and production deployments

### Local Full-Stack Example

**Terminal 1: Backend (ngrok exposed)**

```bash
$env:STREAMLIT_API_URL = 'http://localhost:8000'
.\run_backend.ps1

# In another window, start ngrok
ngrok http 8000
# Note the URL: https://abc-123.ngrok-free.dev
```

**Terminal 2: Streamlit Frontend**

```bash
$env:STREAMLIT_API_URL = 'https://abc-123.ngrok-free.dev'
streamlit run streamlit_app.py
```

---

## 11. Deployment Matrix

| Component          | Environment     | Method                                  | Notes                         |
| ------------------ | --------------- | --------------------------------------- | ----------------------------- |
| Backend            | Google Colab    | colab_deployment.ipynb + ngrok          | GPU, free tier, temporary     |
| Backend            | Local           | run_backend.ps1 / run_backend.sh        | Development, fast iteration   |
| Backend            | Production      | Docker + Render/AWS/Self-host           | Persistent, custom domains    |
| Frontend           | Local           | streamlit run streamlit_app.py          | Development                   |
| Frontend           | Streamlit Cloud | Push to GitHub, connect Streamlit Cloud | Managed, custom domain (paid) |
| Frontend + Backend | Local           | run_backend.ps1 + streamlit run + ngrok | Full-stack dev setup          |

---

## Resources

- [Backend Deployment Details](DEPLOY_BACKEND.md)
- [Architecture Overview](ARCHITECTURE_EXPLAINED.md)
- [Process Overview](PROCESS_OVERVIEW.md)
- [Colab Deployment Notebook](colab_deployment.ipynb)
