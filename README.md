# Startup-Pitch-Evaluation

Multimodal startup pitch evaluation backend with a FastAPI API, shared CLI inference, chunk-level scoring, and optional local/cloud transcription fallbacks.

---

## Project Technical Overview (Presentation Guide)

This section explains **what was built, what packages were used, and what type of ML is involved** — in plain terms suitable for a project review.

### What this project does

Given a startup pitch video (or transcript + slides), the system automatically scores the pitch across **10 quantitative metrics** — things like *Problem Clarity*, *Market Opportunity*, *Voice Pace*, and *Presenter Confidence* — and produces an investor-ready dashboard with an overall score, confidence band, and risk flags.

---

### Type of Machine Learning used

This is a **Multimodal Heuristic Pipeline** — not a single deep neural network. Here is how each part works:

| Layer | ML / AI Technique |
|---|---|
| **Speech-to-Text** | **Transformer-based ASR** — OpenAI Whisper / faster-whisper (encoder-decoder transformer, the same architecture behind GPT but tuned for audio) |
| **Face & Pose Detection** | **Convolutional Neural Networks (CNNs)** — OpenCV's Haar Cascade (classical CNN-style sliding-window detector) and **Google MediaPipe** (lightweight BlazeFace + BlazePose neural networks, optimised for real-time inference on CPU) |
| **Language Detection** | **Probabilistic classifier** — `langdetect` library (Naive Bayes trained on character n-grams), augmented with rule-based Unicode script analysis |
| **Scoring** | **Weighted linear aggregation / scoring rubric** — heuristic rules + learned keyword signals produce per-metric scores (0–10), then blended with configurable weights |
| **Modality Fusion** | **Attention weighting** — softmax-style normalisation of embedding energy to decide how much to trust text vs audio vs video at each moment |
| **Training (optional)** | **Linear Regression trained with Stochastic Gradient Descent (SGD)** — a 16 → 10 linear model with MSE loss; trains on labelled pitch data or synthetic data when real labels are unavailable |

> **Bottom line for your review:** *The core runtime pipeline is a rule-and-heuristic system that calls pre-trained neural models (Whisper, MediaPipe) as sub-components. The optional training module adds a simple linear regression layer on top. There is no end-to-end deep neural network trained from scratch.*

---

### Packages and libraries used

#### Web & API
| Package | Version | Purpose |
|---|---|---|
| **FastAPI** | 0.116.1 | REST API framework (POST /evaluate, batch, streaming) |
| **Uvicorn** | 0.35.0 | ASGI web server that runs the FastAPI app |
| **Pydantic** | 2.11.7 | Request/response schema validation and serialisation |
| **pydantic-settings** | 2.10.1 | `SPE_*` environment variable configuration |
| **httpx** | 0.28.1 | Async HTTP client (used in tests) |

#### Computer Vision — Video Processing
| Package | Version | Purpose |
|---|---|---|
| **OpenCV** (`opencv-python-headless`) | 4.10.0.84 | Frame extraction from video files, Haar Cascade face detection, grayscale motion estimation (frame-diff), JPEG frame saving |
| **MediaPipe** | 0.10.14 | **FaceMesh** (468 facial landmarks → eye-contact score) and **Pose** (33 body landmarks → gesture energy); runs the underlying BlazeFace / BlazePose CNNs |

#### Audio Processing
| Package | Version | Purpose |
|---|---|---|
| **imageio-ffmpeg** | 0.6.0 | Bundles FFmpeg binary; used to extract mono 16 kHz WAV audio chunks from video |
| **Python `wave`** (stdlib) | — | Reads extracted WAV files into raw PCM frames |
| **NumPy** | 2.2.6 | All waveform maths: silence/clipping ratio, RMS energy per frame, autocorrelation-based pitch detection (70–320 Hz), Mel-spectrogram shape estimation |

#### Speech-to-Text (ASR)
| Package | Version | Purpose |
|---|---|---|
| **faster-whisper** | 1.1.1 | Local Whisper transformer (CTranslate2-optimised); supports `tiny` → `large` model sizes; runs on CPU with `int8` quantisation |
| **openai** | 1.108.1 | OpenAI Whisper API (`whisper-1` model) as cloud fallback when local ASR is unavailable |

#### Language Detection
| Package | Version | Purpose |
|---|---|---|
| **langdetect** | 1.0.9 | Probabilistic language identification; used when simple Unicode script ratio is ambiguous. Supports English (`en`), Tamil (`ta`), mixed (`ta-en`) |

#### Utilities
| Package | Version | Purpose |
|---|---|---|
| **NumPy** | 2.2.6 | Embedding vectors (24-dim), attention weight computation, linear regression forward/backward pass |
| `hashlib` (stdlib) | — | SHA-256 deterministic embeddings; MD5 frame/audio cache hashes |
| `concurrent.futures` (stdlib) | — | `ThreadPoolExecutor` with 3 workers for parallel text/audio/video extraction per chunk |
| `subprocess` (stdlib) | — | Runs FFmpeg commands for audio extraction |
| `pathlib` (stdlib) | — | Cross-platform file path handling |
| `dataclasses` (stdlib) | — | Typed data structures for chunk metadata |
| `logging` (stdlib) | — | Structured application logging |

#### Testing & Dev
| Package | Version | Purpose |
|---|---|---|
| **pytest** | 8.4.1 | Unit and integration test suite |
| **JupyterLab** | 4.3.5 | Notebook environment for exploration |

---

### Preprocessing — step by step

```
1. INPUT NORMALISATION
   PitchInput (title, transcript, video metadata, slides, user stage)
       │
       ▼
2. TEMPORAL CHUNKING
   Video duration ÷ 5 seconds = N chunks
   Each chunk = [start_sec, end_sec, text_excerpt, slide_context]
       │
       ▼
3. PER-CHUNK PARALLEL FEATURE EXTRACTION  (3 threads)
   ├── TEXT
   │     • Normalise whitespace
   │     • Detect language (Unicode script ratio → langdetect fallback)
   │     • Tokenise into words, compute unique-word ratio
   │     • Keyword presence flags (market, problem, revenue, team …)
   │     • SHA-256 → 24-dimensional deterministic embedding vector
   │
   ├── AUDIO
   │     • FFmpeg: extract 5-sec WAV chunk (mono, 16 kHz)
   │     • NumPy: normalise PCM int16 → float32 [-1, 1]
   │     • Silence ratio  (|sample| < 0.01)
   │     • Clipping ratio (|sample| ≥ 0.98)
   │     • Frame-based RMS energy (25 ms frames, 10 ms hop)
   │     • Autocorrelation pitch detection → pitch variation
   │     • Optional Whisper transcription (local or cloud)
   │
   └── VIDEO
         • OpenCV VideoCapture: sample 5 evenly-spaced frames
         • Haar Cascade: detect faces per frame
         • MediaPipe FaceMesh: nose-tip X → eye-contact score
         • MediaPipe Pose: wrist/shoulder Y-displacement → gesture energy
         • Grayscale frame-diff → motion score
         • Save frames as JPEG to outputs/frames/
       │
       ▼
4. MODALITY FUSION
   Compute embedding energy (mean of 24-dim vector) for each modality
   Softmax → attention weights (text_w, audio_w, visual_w)
   Weighted blend → 24-dim fused embedding
       │
       ▼
5. SCORING  (10 metrics, 0–10 scale)
   Text metrics (weight 0.50):
     Problem Clarity, Market Opportunity, Solution Uniqueness,
     Traction Evidence, Business Model Strength, Team Readiness
   AV metrics (weight 0.35):
     Voice Pace, Voice Prosody, Delivery Clarity, Presenter Confidence
   Fusion signal (weight 0.15):
     Attention-weighted embedding mean
       │
       ▼
6. RISK FLAGGING  (heuristic rules)
   • Low aggregate score  < 5.5
   • Missing competitive analysis ("no competition" phrase)
   • Overclaims ("guaranteed", "100%")
   • Weak traction evidence ("soon" without "revenue")
       │
       ▼
7. AGGREGATION & OUTPUT
   Average chunk scores → overall_score, confidence_score
   Threshold → investment_band (high-potential ≥ 8.0 / watchlist / early-risk)
   Build investor dashboard (metric trends, modality weights, risk distribution)
```

---

### Key design decisions worth mentioning in review

1. **No GPU required** — all neural sub-models (MediaPipe, faster-whisper int8) run on CPU, making the system portable and cloud-deployable without GPU instances.
2. **Deterministic fallbacks** — every feature extractor has a hash-based fallback so the API always returns a result even when the video file is missing or ffmpeg is not installed.
3. **Multilingual support** — the pipeline natively handles English, Tamil, and mixed Tamil-English transcripts with separate scoring bonuses for bilingual pitches.
4. **Temporal granularity** — scoring at 5-second chunk level lets investors see *where* in the pitch confidence or clarity dropped, not just a single aggregate number.
5. **Modular architecture** — text / audio / video encoders are independent classes; swapping in a real BERT or wav2vec model later requires changing only one class.

---

## Current status

- FastAPI service with single and batch pitch evaluation
- Shared inference engine used by API and CLI (`InferenceService`)
- 5-second timeline chunking with synchronized text/audio/visual metadata
- Deterministic fallback behavior when AV dependencies or media files are unavailable
- Optional local faster-whisper and OpenAI Whisper API transcription paths
- Static frontend served by the API root route
- Training, evaluation, and runtime benchmark scripts

## Architecture summary

1. Input payload is normalized (title, transcript/video text, slides, user details).
2. Preprocessing creates chunk windows (`window_seconds=5` by default).
3. Per chunk, text/visual/audio features are extracted in parallel.
4. Modalities are fused into attention weights and scored into 10 quantitative metrics.
5. Risk flags, strengths/weaknesses/suggestions, and dashboard series are generated.

## Project structure

```text
.
├── backend/
│   ├── app/
│   │   ├── core/config.py
│   │   ├── main.py
│   │   ├── pipeline.py
│   │   ├── schemas.py
│   │   ├── services/
│   │   │   ├── inference.py
│   │   │   ├── preprocessing.py
│   │   │   ├── transcriber.py
│   │   │   ├── audio_processor.py
│   │   │   ├── video_processor.py
│   │   │   ├── extractors.py
│   │   │   ├── fusion.py
│   │   │   ├── scoring.py
│   │   │   ├── risk.py
│   │   │   └── reporting.py
│   │   └── static/
│   ├── models/
│   │   ├── config/
│   │   └── checkpoints/
│   ├── scripts/
│   │   ├── infer_cli.py
│   │   ├── train.py
│   │   ├── evaluate.py
│   │   └── benchmark_runtime.py
│   ├── tests/
│   ├── training/
│   └── requirements.txt
├── LICENSE
└── README.md
```

## Quick start (Windows PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Service URLs:

- `http://127.0.0.1:8000/` (static frontend)
- `http://127.0.0.1:8000/docs` (OpenAPI docs)
- `http://127.0.0.1:8000/health`

## API endpoints

- `GET /health` - service health/version
- `GET /` - serves frontend UI (`backend/app/static/index.html`)
- `POST /evaluate` - evaluate one pitch (`PitchInput`)
- `POST /evaluate/batch` - evaluate list of pitches (`BatchEvaluationRequest`)
- `GET /videos` - list videos from `backend/outputs/batch_input`
- `GET /videos/{video_name}` - stream one video from batch input directory

## Request/response highlights

Input model (`PitchInput`) supports:

- `title`, `transcript`, `language_hint`
- `video` (`file_name`, `file_format`, `duration_sec`, `transcript_text`)
- `slides` and/or `slide_text`
- `presenter_profile` and `user_details`

Response (`EvaluationResponse`) includes:

- `summary.overall_score`, `summary.confidence_score`
- `summary.investment_band` (`high-potential`, `watchlist`, `early-risk`)
- `summary.language_detected` (`en`, `ta`, `ta-en`)
- `summary.processing_option` and `summary.processing_notes`
- `chunk_reports[]` with metric-level scores, attention, and risk flags
- `dashboard` series for quantitative metrics, modality weights, and risk distribution

## CLI usage

All scripts run from `backend/`.

Single-video inference:

```powershell
python scripts/infer_cli.py --video outputs/batch_input/sample.mp4 --duration-sec 90 --language-hint en-ta --output outputs/sample_eval.json
```

Batch-video inference:

```powershell
python scripts/infer_cli.py --batch-dir outputs/batch_input --duration-sec 90 --batch-output-dir outputs/batch_results --output outputs/batch_summary.json
```

Train:

```powershell
python scripts/train.py --config models/config/training_cpu.yaml
```

Evaluate checkpoint:

```powershell
python scripts/evaluate.py --config models/config/training_cpu.yaml --checkpoint models/checkpoints/training_cpu_checkpoint.json
```

Benchmark runtime:

```powershell
python scripts/benchmark_runtime.py --runs 5 --duration-sec 60 --output outputs/benchmark_runtime.json
```

## Configuration

Environment variables use the `SPE_` prefix and are loaded from `.env` at repository root and/or `backend/.env`.

Core flags:

```text
SPE_USE_HEURISTIC_PIPELINE=true
SPE_USE_LOCAL_TRANSCRIBER=true
SPE_ENABLE_VISUAL_EXTRACTION=true
SPE_ENABLE_AUDIO_EXTRACTION=true
SPE_CHUNK_WINDOW_SECONDS=5
SPE_MEDIA_LOOKUP_DIR=outputs/batch_input
```

Transcriber selection:

```text
SPE_TRANSCRIBER_BACKEND=auto
SPE_TRANSCRIBER_MIN_AUDIO_QUALITY=0.35
SPE_FASTER_WHISPER_MODEL_SIZE=small
SPE_FASTER_WHISPER_DEVICE=cpu
SPE_FASTER_WHISPER_COMPUTE_TYPE=int8
SPE_OPENAI_API_KEY=
SPE_OPENAI_TRANSCRIBER_MODEL=whisper-1
```

Notes:

- `auto` transcriber mode tries local faster-whisper first, then OpenAI Whisper API.
- `SPE_MEDIA_LOOKUP_DIR` is resolved relative to `backend/` unless absolute.
- Audio extraction uses ffmpeg; if not on PATH, `imageio-ffmpeg` fallback is attempted.

## Tests

```powershell
cd backend
pytest -q
```

The current suite covers API parity with shared inference, pipeline response shape, language detection behavior, transcriber fallback behavior, and audio/video processor fallback safety.

## Notes for contributors

- Keep API schema changes backward-compatible where possible.
- Keep API and CLI behavior consistent through `app/services/inference.py`.
- Update docs and tests whenever endpoint behavior or configuration semantics change.
