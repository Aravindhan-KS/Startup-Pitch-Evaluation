# Quick Start - Colab + ngrok

## 3-Step Setup

### 1. Prepare
- Put 1-2 short sample videos in `backend/outputs/batch_input/`.
- Open [colab_deployment.ipynb](colab_deployment.ipynb).
- In Colab, switch runtime to GPU.
- Get your ngrok auth token from https://dashboard.ngrok.com/auth/your-authtoken.

### 2. Run the notebook
Run the cells in order:
1. GPU/system check
2. System package install
3. Python dependency install
4. Repo preparation
5. ngrok token setup
6. Check model checkpoint
7. Start FastAPI + ngrok
8. Test health and evaluation

### 3. Use the live URL
The notebook prints a public ngrok URL. Use it for:
- `GET /health`
- `GET /docs`
- `POST /evaluate`
- `POST /evaluate/upload`

## What you get
- GPU-backed inference in Colab
- Same preprocessing, extraction, fusion, and scoring pipeline as local
- Temporary public access through ngrok

## Important
- Keep the Colab tab open.
- If Colab disconnects, the ngrok URL changes.
- Start again from the ngrok/token cell if needed.
