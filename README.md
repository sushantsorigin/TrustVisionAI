🛡️ TrustVision AI
AI-powered deepfake detection for face images
Upload a photo or capture one from your webcam, get an authenticity verdict with a confidence score, and download a PDF report.
---
Overview
Generative AI makes it easy to fabricate realistic faces. TrustVision AI is a full-stack web app that screens a face image with a pretrained deep-learning classifier, combines that score with lightweight metadata and image-forensics signals, and presents the result in a clean interface.
It was built as a student project to show how a modern ML model can be served through a REST API and a React front end. It is a screening aid, not proof: see Limitations.
Features
🖼️ Image upload with drag-and-drop
📷 Webcam capture, with live frame sampling from the browser
📊 Authenticity score, prediction (REAL / FAKE), confidence and risk level (LOW / MEDIUM / HIGH)
🔬 Forensic signals: EXIF / AI-generation metadata checks, plus texture, edge, DCT and ELA analysis when running locally
📄 PDF report for every scan
💾 Scan history stored in SQLite
🤖 Optional Gemini Vision second opinion (off unless an API key is set)
🔌 Two inference modes: local PyTorch, or remote Hugging Face Inference API
How it works
```text
User
 │
 ▼
React + Vite frontend
 │  POST /scan (multipart file)
 ▼
FastAPI backend ──────────────► SQLite (scan history)
 │            └───────────────► PDF report (/reports/{id})
 ├── local mode ──► PyTorch + SigLIP + OpenCV forensics
 ├── remote mode ─► Hugging Face Inference API
 └── optional ────► Gemini Vision second opinion
```
The frontend sends the image to `POST /scan`.
The backend runs the detector (local or remote) and reads image metadata.
Neural scores are fused with metadata and forensic signals into a final prediction.
The scan is saved to SQLite and the JSON result is returned. A PDF is available at `/reports/{id}`.
If inference fails, the API returns an error. It does not return a made-up prediction.
Tech stack
Layer	Technology
Frontend	React 19, Vite, Tailwind CSS 4, React Router, Framer Motion
Backend	FastAPI, SQLAlchemy, SQLite, ReportLab, Pillow
ML	PyTorch, Hugging Face Transformers, OpenCV, SciPy
Model	`prithivMLmods/deepfake-detector-model-v1` (SigLIP, Apache-2.0)
Optional	Google Gemini Vision
Deployment	Vercel (frontend), Render (backend)
Project structure
```text
TrustVision-AI/
├── Frontend/            React app (pages/Home, pages/Analyze)
├── Backend/
│   ├── main.py          FastAPI routes
│   └── reporting.py     PDF report generation
├── database/            SQLAlchemy engine and models
├── ml/
│   ├── inference.py     Detector (local + remote) and score fusion
│   ├── gemini_verifier.py
│   └── runtime_config.py
├── test_images/         Sample images
├── app.py               Deployment entrypoint
├── start_app.py         Starts backend and frontend together
├── requirements.txt     Lightweight API dependencies (remote inference)
└── requirements-ml.txt  Full local ML dependencies
```
Getting started
Prerequisites
Python 3.10+
Node.js 18+ and npm
1. Clone
```bash
git clone https://github.com/sushantsorigin/TrustVisionAI.git
cd TrustVisionAI
```
2. Install backend dependencies
Pick one:
```bash
# Local inference (downloads the model on first run; needs several GB of RAM/disk)
pip install -r requirements-ml.txt

# Remote inference only (lightweight, needs a Hugging Face token)
pip install -r requirements.txt
```
3. Install frontend dependencies
```bash
cd Frontend
npm install
cd ..
```
4. Run
```bash
python start_app.py
```
Frontend: http://localhost:5173
Backend: http://localhost:8000
API docs: http://localhost:8000/docs
Or run them separately:
```bash
python -m uvicorn Backend.main:app --reload    # backend
cd Frontend && npm run dev                      # frontend
```
The Vite dev server proxies `/scan` and `/reports` to the backend.
Configuration
Set these as environment variables (a `Backend/.env` file is loaded automatically and is git-ignored). Never commit keys.
Variable	Purpose	Default
`TRUSTVISION_INFERENCE_BACKEND`	`local`, `remote` or `auto`	`auto`
`HF_TOKEN`	Hugging Face token for remote inference	none
`HF_INFERENCE_URL`	Override the remote inference endpoint	HF router URL for the model
`HF_INFERENCE_TIMEOUT`	Remote request timeout in seconds	`45`
`GEMINI_API_KEY` / `GEMINI_API_KEYS`	Enable optional Gemini verification (comma-separated list for rotation)	none
`GEMINI_MODEL`	Gemini model name	`gemini-2.0-flash` (see note below)
`CORS_ALLOW_ORIGINS`	Comma-separated allowed origins	`*`
`VITE_API_BASE_URL`	Frontend: backend URL when deployed separately	empty (same origin)
> **Note:** Google has been retiring older Gemini models. If Gemini verification fails, set `GEMINI_MODEL` to a currently available model.
API
Method	Endpoint	Description
`GET`	`/`	Welcome message
`GET`	`/health`	Service and model status
`GET`	`/model-info`	Model metadata
`POST`	`/scan`	Analyze an image (multipart form, field name `file`)
`GET`	`/reports/{id}`	Download the PDF report for a scan
Example:
```bash
curl -X POST http://localhost:8000/scan -F "file=@test_images/sample.jpg"
```
Response (abridged):
```json
{
  "id": 1,
  "prediction": "REAL",
  "authenticity_score": 87.4,
  "confidence": 87.4,
  "risk_level": "LOW",
  "real_probability": 87.4,
  "fake_probability": 12.6,
  "report_url": "/reports/1"
}
```
Deployment
Frontend (Vercel): set the project root to `Frontend`, and set `VITE_API_BASE_URL` to your backend URL.
Backend (Render): deploy the repo as a Python web service and run `uvicorn Backend.main:app --host 0.0.0.0 --port $PORT`. Set `CORS_ALLOW_ORIGINS` to your frontend URL.
> The free Render tier has 512 MB RAM, which is too small to run the PyTorch model locally. That is why the backend defaults to remote inference there.
Limitations
Not forensic proof. The model reports probabilities. It can be wrong in both directions and should not be used as the sole basis for any serious decision.
Accuracy figures are the model author's. The model card reports about 94% accuracy on its own test split and labels the model experimental. Performance on other image types, such as new generators or heavily compressed photos, may be lower.
Remote inference depends on Hugging Face quotas. Free accounts get a small monthly credit allowance, so heavy use can return `402` errors.
Faces only. The model is designed for face imagery.
Heatmaps are not supported for the SigLIP model.
Scan history is not durable on free hosting, where SQLite storage is ephemeral.
Images are sent to third parties when remote inference or Gemini verification is enabled.
There is no user authentication yet, and video upload is not part of the UI.
Roadmap
[ ] Self-hosted or in-browser inference to remove the third-party quota dependency
[ ] Server-side upload size and type validation with structured error responses
[ ] Health check that confirms the model is actually ready
[ ] Evaluation script with precision, recall and F1 on a labeled test set
[ ] User accounts and persistent scan history
Contributing
Issues and pull requests are welcome. For larger changes, open an issue first to discuss what you would like to change.
License
Released under the MIT License.
Acknowledgements
prithivMLmods/deepfake-detector-model-v1 for the pretrained detector
Hugging Face Transformers, FastAPI and React
