# Quick Reference - Colab + ngrok

## Start
1. Open [colab_deployment.ipynb](colab_deployment.ipynb).
2. Set Colab runtime to GPU.
3. Paste your ngrok auth token when prompted.
4. Run the cells in order.

## URLs once running
- Health: `https://YOUR_NGROK_URL/health`
- Docs: `https://YOUR_NGROK_URL/docs`
- UI: `https://YOUR_NGROK_URL/`
- Evaluate: `POST https://YOUR_NGROK_URL/evaluate`
- Upload: `POST https://YOUR_NGROK_URL/evaluate/upload`

## Data flow
Video -> preprocess -> audio/video extraction -> feature extraction -> fusion -> scoring

## Keep in mind
- Colab is temporary.
- ngrok URLs can change when the session restarts.
- The notebook must stay open for the API to remain live.
