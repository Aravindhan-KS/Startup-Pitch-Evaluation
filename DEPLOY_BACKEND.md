# Deploy FastAPI Backend

Steps to run the backend API locally and expose it publicly.

## Local Development

### 1. Create (or activate) a Python environment

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# Linux/Mac
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Run the FastAPI app

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

Test the health endpoint:

```bash
curl http://localhost:8000/health
```

---

## Public Exposure with ngrok

### 1. Install ngrok

Download from https://ngrok.com/download or install via package manager:

```bash
# macOS
brew install ngrok

# Windows (via scoop)
scoop install ngrok

# Or download directly from ngrok.com
```

### 2. Authenticate ngrok

Get your auth token from https://dashboard.ngrok.com/auth/your-authtoken

```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

### 3. Start ngrok tunnel (in a separate terminal)

While the FastAPI app is running on `localhost:8000`:

```bash
ngrok http 8000
```

ngrok will output a public URL like:

```
https://abc-123-def.ngrok-free.dev
```

### 4. Use the ngrok URL

Copy the public URL and use it as the backend for your Streamlit frontend:

```powershell
# Set the backend API URL for Streamlit
$env:STREAMLIT_API_URL='https://abc-123-def.ngrok-free.dev'
streamlit run streamlit_app.py
```

---

## Docker Deployment

Build and run the backend in Docker:

### 1. Create a Dockerfile (if not present)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY backend ./backend
WORKDIR /app/backend

# Expose port
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Build the Docker image

```bash
docker build -t startup-pitch-api:latest .
```

### 3. Run the container

```bash
docker run -p 8000:8000 \
  -v $(pwd)/backend/models:/app/backend/models \
  -v $(pwd)/backend/outputs:/app/backend/outputs \
  startup-pitch-api:latest
```

---

## Custom Domain (Production)

### Option 1: Streamlit Cloud + Render.com

1. Deploy backend to Render.com:
   - Push your repo to GitHub
   - Connect Render account
   - Create new Web Service from GitHub
   - Set build command: `pip install -r backend/requirements.txt`
   - Set start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - Render will assign a public URL like `https://startup-pitch-api-xxxxx.onrender.com`

2. In Streamlit Cloud:
   - Set the Streamlit secrets (or environment variable) to your Render backend URL
   - Streamlit automatically picks up `api_url` from `~/.streamlit/secrets.toml` or env `STREAMLIT_API_URL`

### Option 2: Self-Hosted with nginx + TLS

1. Run the backend on a server (VPS, AWS EC2, DigitalOcean, etc.)
   - Run the FastAPI app (e.g., on port 8000)

2. Configure nginx as a reverse proxy:

```nginx
server {
    server_name api.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. Set up TLS with Certbot:

```bash
sudo certbot certonly --nginx -d api.example.com
```

4. In your Streamlit app, set `STREAMLIT_API_URL='https://api.example.com'`

---

## Environment Variables

- `USE_HEURISTIC_PIPELINE`: Set to `true` for fast heuristic scoring (no ML model needed). Default: `false` (uses neural network if model available).
- `CHUNK_WINDOW_SECONDS`: Duration in seconds for audio/video chunks. Default: `5`.
- `USE_LOCAL_TRANSCRIBER`: Use local Whisper model instead of external API. Default: `false`.

Example:

```bash
export USE_HEURISTIC_PIPELINE=true
export CHUNK_WINDOW_SECONDS=5
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Troubleshooting

### 502 Bad Gateway (nginx)

- Check backend is running: `curl http://127.0.0.1:8000/health`
- Verify nginx config: `sudo nginx -t`
- Check nginx logs: `sudo tail -f /var/log/nginx/error.log`

### ngrok tunnel keeps disconnecting

- Free ngrok tunnels expire after 2 hours. Use ngrok pro for persistent URLs.
- For development, keep the terminal window open.

### Backend API unreachable from Streamlit

- Verify `STREAMLIT_API_URL` is set and accessible
- Open browser DevTools → Network tab, check the failing request URL
- Test directly: `curl https://YOUR_API_URL/health`

---

## Next Steps

- [Deploy Streamlit Frontend](DEPLOY_STREAMLIT.md)
- [Full Architecture](ARCHITECTURE_EXPLAINED.md)
