# TrustVision AI

TrustVision AI is a face-image authenticity analysis project built with:

- `FastAPI` for the backend API
- `React + Vite + Tailwind CSS` for the frontend
- Hugging Face Inference API on Vercel, or local `PyTorch` for full local inference
- `SQLite` for scan history
- `ReportLab` for PDF report export

This repository currently supports:

- Image upload analysis
- Webcam frame sampling from the browser
- Authenticity score, prediction, confidence, and risk level
- PDF report download

This repository does **not** currently implement:

- User authentication
- PostgreSQL
- Video file upload and end-to-end video analysis in the UI
- Enterprise dashboards or role-based access control

## Project Layout

```text
TrustVision-AI/
  Backend/              FastAPI routes and PDF reporting
  Frontend/             React application
  database/             SQLAlchemy database setup and models
  ml/                   Core inference logic and ML model weights
  app.py                FastAPI deployment entrypoint
  gradio_app.py         Gradio UI demo
  requirements.txt      Production/Vercel Python dependencies
  requirements-ml.txt   Full local ML inference dependencies
  requirements-gradio.txt Standalone Gradio demo dependencies
  demo.py               Command-line interface (CLI) image scan demo
  start_app.py          Starts backend and frontend together
```

## How to Run the Project

### Prerequisites
- **Python 3.10+**
- **Node.js & npm**

### 1. Install Dependencies
Install the production Python backend dependencies:
```bash
pip install -r requirements.txt
```

For full local PyTorch/OpenCV inference, install the ML dependency set instead:
```bash
pip install -r requirements-ml.txt
```

If you install only the production dependencies, the backend uses Hugging Face remote inference and requires an `HF_TOKEN` with inference access. Set it in the environment before starting the backend. To avoid remote inference, install `requirements-ml.txt`; the model will then be downloaded from Hugging Face on first startup.

Install the React frontend dependencies:
```bash
cd Frontend
npm install
cd ..
```

### 2. Start the Application
You can start both the FastAPI backend and the React frontend simultaneously using the provided startup script. From the repository root, run:
```bash
python start_app.py
```
This script will automatically launch:
- **Backend API:** `http://localhost:8000`
- **Frontend UI:** `http://localhost:5173`

The Vite development server proxies `/scan` and `/reports` requests to the local backend.

*(Press `Ctrl+C` in the terminal to stop all services.)*

Alternatively, you can run them manually in separate terminal windows:
- **Backend:** `python -m uvicorn Backend.main:app --reload`
- **Frontend:** `cd Frontend && npm run dev`

### Optional Gemini Verification
To enable the optional Gemini secondary verifier, set one of these environment variables before starting the backend:
```bash
GEMINI_API_KEY=your_key_here
```
For key rotation, set `GEMINI_API_KEYS` to a comma-separated list. Do not hardcode API keys in source files.

### Vercel Deployment
The root `app.py` exports the FastAPI `app` for Vercel. Vercel uses `requirements.txt`, Python 3.12, `/tmp/trustvision.db` for SQLite, and the remote Hugging Face inference backend by default.

Recommended Vercel environment variables:
```bash
HF_TOKEN=your_huggingface_token
GEMINI_API_KEY=your_optional_gemini_key
```

If you deploy the frontend separately, set `VITE_API_BASE_URL` to the deployed backend URL before building the frontend. If the frontend and backend share the same origin, leave it empty.

## Optional Demos

### Gradio Web UI
A lightweight Gradio web interface is available for quickly testing the model outside the main application:
```bash
pip install -r requirements-gradio.txt
python gradio_app.py
```

### CLI Image Scan
You can easily scan an image from the terminal with a simple command:
```bash
python demo.py --image path/to/file.jpg
```
Heatmap generation is not currently supported with the new SigLip model integration.

## License

MIT
