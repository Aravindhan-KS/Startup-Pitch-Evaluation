# LOCAL EDGE + CLOUD DASHBOARD QUICK START

## Architecture Overview

```
EDGE DEVICE (Local)          CLOUD DATABASE            DASHBOARD (Cloud)
─────────────────────        ───────────────           ─────────────────
Camera/Video → FastAPI       Firebase Firestore        Streamlit Cloud
Backend → Processes          (Stores Results)          (Displays Results)
↓
CloudUploader
↓
Firebase
```

---

## PART 1: LOCAL BACKEND SETUP

### 1.1 Install Python Dependencies

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 1.2 Configure Environment

Copy the example config:

```bash
cd backend
copy ..\env.example .env
# OR on macOS/Linux:
cp ../.env.example .env
```

Edit `.env` with your settings:

- `SPE_USE_HEURISTIC_PIPELINE=true` (for demo/CPU)
- `SPE_FASTER_WHISPER_DEVICE=cpu` (for CPU edge device)
- `FIREBASE_KEY_PATH=firebase_key.json` (path to Firebase key)

### 1.3 Add Firebase Key (Optional for Cloud Upload)

To enable automatic cloud upload:

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project (or create one)
3. Go to **Settings → Service Accounts**
4. Click **Generate new private key**
5. Save JSON file as `backend/firebase_key.json`

**IMPORTANT:** Add to `.gitignore` (already done in the repo)

### 1.4 Start Backend Server

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Or with auto-reload for development:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:

- **Dashboard:** http://127.0.0.1:8000/docs
- **Health check:** http://127.0.0.1:8000/health
- **Evaluation endpoint:** POST http://127.0.0.1:8000/evaluate

---

## PART 2: LOCAL EDGE CAMERA RUNNER

### 2.1 Configure Edge Camera Settings

Copy edge config:

```bash
copy .env.edge.example .env.edge
# OR on macOS/Linux:
cp .env.edge.example .env.edge
```

Edit `.env.edge`:

- `EDGE_CAMERA_URL=0` (for webcam)
- `EDGE_BACKEND_URL=http://127.0.0.1:8000/evaluate` (backend URL)
- `EDGE_RECORD_DURATION=30` (clip length)
- `EDGE_CAPTURE_INTERVAL=10` (wait between captures)

### 2.2 Run Camera Capture

In a **NEW terminal** (keeping backend running in first terminal):

```bash
cd backend
.\.venv\Scripts\Activate.ps1  # Windows
# OR
source .venv/bin/activate     # macOS/Linux

python app/edge/camera_runner.py
```

This will:

1. Open your camera/webcam
2. Record 30-second clips
3. Send to backend for evaluation
4. Upload results to Firebase (if key configured)

**Keyboard Control:**

- Press `Q` in preview window to stop recording

---

## PART 3: STREAMLIT CLOUD DASHBOARD

### 3.1 Install Streamlit Locally (for testing)

```bash
pip install -r requirements-streamlit.txt
```

### 3.2 Configure Secrets

Create or edit `.streamlit/secrets.toml`:

```toml
[firebase]
type = "service_account"
project_id = "your-project-id"
private_key_id = "xxxx"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/certificates/..."
```

Use the same Firebase key as the backend.

### 3.3 Test Locally

```bash
streamlit run streamlit_app.py
```

Dashboard will open at: http://localhost:8501

### 3.4 Deploy to Streamlit Cloud

1. Commit to GitHub:

```bash
git add streamlit_app.py requirements-streamlit.txt
git commit -m "Add edge cloud dashboard"
git push
```

2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Click **New app** → Select your GitHub repo
4. Choose branch and `streamlit_app.py`
5. Go to **Settings → Secrets** → Paste your `secrets.toml` content
6. Click **Deploy**

---

## PART 4: COMPLETE WORKFLOW

### Terminal 1: Start Backend

```bash
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Terminal 2: Start Edge Camera Runner

```bash
cd backend
.\.venv\Scripts\Activate.ps1
python app/edge/camera_runner.py
```

### Terminal 3: Local Dashboard (optional)

```bash
streamlit run streamlit_app.py
```

### Cloud: Streamlit Cloud Dashboard

Your app will be live at: `https://your-username-your-app-name.streamlit.app`

---

## TROUBLESHOOTING

### Backend won't start

```bash
# Check if port 8000 is in use
# Kill process or use different port:
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Camera won't open

```bash
# Check camera device:
# On Windows: Test with Camera app first
# On Linux: ls /dev/video*
# Change EDGE_CAMERA_URL in .env.edge
```

### Firebase upload fails

```bash
# Check firebase_key.json exists in backend/
# Verify FIREBASE_KEY_PATH in .env
# Check Firebase database is created in console
```

### Streamlit won't connect to Firebase

```bash
# Verify secrets.toml has correct Firebase key
# Check [firebase] section is properly formatted
# Use same key as backend
```

---

## ENVIRONMENT VARIABLES SUMMARY

### Backend (.env)

```
FIREBASE_KEY_PATH=firebase_key.json
SPE_USE_HEURISTIC_PIPELINE=true
SPE_USE_LOCAL_TRANSCRIBER=true
SPE_ENABLE_VISUAL_EXTRACTION=true
SPE_ENABLE_AUDIO_EXTRACTION=true
SPE_FASTER_WHISPER_DEVICE=cpu
SPE_FASTER_WHISPER_COMPUTE_TYPE=int8
SPE_CHUNK_WINDOW_SECONDS=30
SPE_MEDIA_LOOKUP_DIR=outputs/batch_input
SPE_NN_DEVICE=cpu
```

### Edge Camera Runner (.env.edge)

```
EDGE_CAMERA_URL=0
EDGE_BACKEND_URL=http://127.0.0.1:8000/evaluate
EDGE_RECORD_DURATION=30
EDGE_CAPTURE_INTERVAL=10
EDGE_OUTPUT_DIR=outputs/batch_input
```

### Streamlit Cloud

- Set in: **Settings → Secrets → secrets.toml**
- Must have `[firebase]` section with service account key

---

## NEXT STEPS

1. ✅ **Set up local backend** → Test with `curl localhost:8000/health`
2. ✅ **Configure Firebase** → Create project and service account
3. ✅ **Test edge camera runner** → Verify videos are captured and evaluated
4. ✅ **Test local Streamlit dashboard** → Verify data flows from Firebase
5. ✅ **Deploy to Streamlit Cloud** → Set secrets and deploy
6. ✅ **Monitor production** → Keep backend running, watch dashboard

---

## FILES CHANGED

New files:

- `backend/app/services/cloud_uploader.py` - Firebase uploader
- `backend/app/edge/camera_runner.py` - Edge camera capture
- `backend/app/edge/__init__.py` - Edge module init
- `.streamlit/secrets.toml.example` - Secrets template
- `.env.edge.example` - Edge runner config example
- `EDGE_CLOUD_SETUP.md` - This file

Modified files:

- `backend/app/main.py` - Added cloud upload to endpoints
- `streamlit_app.py` - Converted to cloud dashboard
- `backend/requirements.txt` - Added firebase-admin
- `requirements-streamlit.txt` - Added firebase-admin, pandas
- `.gitignore` - Added firebase_key.json, secrets

---

## SYSTEM ARCHITECTURE EXPLANATION

> The proposed system uses a local edge device for real-time video capture and multimodal pitch evaluation. The local backend performs video, audio, and text-based feature extraction using the FastAPI inference pipeline. Instead of streaming full video to the cloud, only processed evaluation results such as overall score, confidence score, investment band, strengths, weaknesses, and dashboard metrics are uploaded to Firebase. The Streamlit Cloud dashboard retrieves these results and visualizes them in real time.

This architecture is **efficient**, **secure**, and **scalable**:

- ✅ Processes heavy compute locally
- ✅ Only transmits lightweight JSON results to cloud
- ✅ Suitable for Streamlit Cloud's limitations
- ✅ Works with limited internet bandwidth
- ✅ Scales to multiple edge devices
