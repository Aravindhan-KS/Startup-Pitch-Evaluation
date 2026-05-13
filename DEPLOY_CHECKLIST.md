# Colab + ngrok Deploy Checklist

## What This Setup Does

This deploys the FastAPI backend in Google Colab using a GPU runtime, then exposes it publicly through ngrok.

Use the notebook: [colab_deployment.ipynb](colab_deployment.ipynb)

---

## Pre-Deployment

- [ ] **Check the model files exist**

  ```bash
  ls -la backend/models/checkpoints/
  # Expected: phase6_gpu_nn_model.pt
  ```

- [ ] **Add 1-2 sample videos** to `backend/outputs/batch_input/`
  - Use short clips, about 30-60 seconds each
  - Example: `sample_pitch_1.mp4`

- [ ] **Make sure the notebook is ready**
  - Open `colab_deployment.ipynb`
  - In Colab, switch runtime to GPU: Runtime -> Change runtime type -> T4 GPU

- [ ] **Get your ngrok auth token**
  - Copy it from: https://dashboard.ngrok.com/auth/your-authtoken

---

## Colab Setup

- [ ] **Open the notebook in Colab**
  - Upload `colab_deployment.ipynb` to Google Colab
  - Or open it from GitHub if the repo is public

- [ ] **Run the cells in order**
  1. Check GPU and system info
  2. Install system dependencies
  3. Install Python dependencies
  4. Prepare the repo in Colab
  5. Configure the ngrok token
  6. Verify the model checkpoint
  7. Start FastAPI and create the ngrok tunnel
  8. Test health and evaluation endpoints

- [ ] **Keep Colab open**
  - The API only stays live while the notebook session is active
  - If Colab disconnects, the ngrok URL can change

---

## After You Start the Server

- [ ] **Copy the public ngrok URL** printed by the notebook
- [ ] **Test the health endpoint**

  ```bash
  curl https://YOUR_NGROK_URL/health
  ```

- [ ] **Test the evaluation endpoint**

  ```bash
  curl -X POST "https://YOUR_NGROK_URL/evaluate" \
    -H "Content-Type: application/json" \
    -d '{"title":"Sample Pitch","transcript":"We solve X problem","language_hint":"en"}'
  ```

- [ ] **Open the frontend/UI if needed**
  ```text
  https://YOUR_NGROK_URL/
  ```

---

## What Happens in Colab

### Cell 1: GPU Check

Confirms the runtime is using a GPU and that ffmpeg is available.

### Cell 2: System Packages

Installs ffmpeg and image libraries needed for video/audio processing.

### Cell 3: Python Packages

Installs the API, ML, audio, and ngrok dependencies.

### Cell 4: Repo Preparation

Prepares the repo files needed by the FastAPI app and evaluation flow.

### Cell 5: ngrok Token

Registers your token so ngrok can create a public tunnel.

### Cell 6: Checkpoint Verification

Confirms the neural checkpoint exists before starting the server.

### Cell 7: Start API + Tunnel

Starts Uvicorn on port 8000 and exposes it through ngrok.

### Cell 8-9: Smoke Tests

Checks `/health` and `/evaluate` to confirm the pipeline works.

---

## Data Processing Flow

When the API receives a pitch, it still runs the same pipeline as local:

1. **Preprocessing** - chunk the pitch and resolve media paths
2. **Extraction** - read audio and frames from the video
3. **Feature extraction** - compute text, visual, and audio features
4. **Fusion** - combine the modalities
5. **Scoring** - return risk, pitch, and strength outputs

Because Colab gives you a GPU, the neural path is available when the checkpoint and dependencies are present.

---

## Common Issues

- [ ] **GPU not available**
  - Change Colab runtime type to GPU and rerun the notebook

- [ ] **ngrok tunnel failed**
  - Re-run the token cell and confirm the token is valid

- [ ] **Model checkpoint not found**
  - Confirm `backend/models/checkpoints/phase6_gpu_nn_model.pt` exists in the Colab workspace

- [ ] **Colab disconnects**
  - Restart from Cell 5 onward and ngrok will issue a new URL

- [ ] **Slow responses**
  - GPU helps, but first request may still be slower while models load

---

## Keep Handy

- Notebook: [colab_deployment.ipynb](colab_deployment.ipynb)
- ngrok auth token page: https://dashboard.ngrok.com/auth/your-authtoken
- Colab runtime GPU: Runtime -> Change runtime type -> GPU
- API docs once running: `https://YOUR_NGROK_URL/docs`

3. **Customize frontend**
   - Edit `backend/app/static/index.html`
   - Edit `backend/app/static/app.js`
   - Push changes to deploy

4. **Scale up** (if needed)
   - Upgrade to "Starter" or "Pro" plan
   - Enable full neural network mode
   - Disable heuristic fallbacks

---

## Support

- **ngrok Docs**: https://ngrok.com/docs
- **FastAPI Docs**: `http://127.0.0.1:8000/docs` inside Colab, or `https://YOUR_NGROK_URL/docs` after the tunnel is live
- **Local Testing**: `cd backend && uvicorn app.main:app --reload`
