# 🛡️ TrustVision AI
### AI-Powered Deepfake Detection & Digital Media Verification

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge&logo=react)
![Vite](https://img.shields.io/badge/Vite-Build-646CFF?style=for-the-badge&logo=vite)
![PyTorch](https://img.shields.io/badge/PyTorch-ML-EE4C2C?style=for-the-badge&logo=pytorch)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

TrustVision AI is a web application that screens face images for signs of AI generation or manipulation using a pretrained deep-learning model. Users can upload or capture an image, receive an authenticity analysis with confidence scores, and download a PDF report.

---

## 📖 Overview

Generative AI has made it increasingly difficult to tell authentic photos from synthetic ones. TrustVision AI combines computer vision, deep learning and modern web technologies into a simple detection platform.

The application consists of a React frontend, a FastAPI backend, and an inference engine built on PyTorch and Hugging Face Transformers. Neural predictions are combined with image-metadata and forensic signals to produce the final result.

> **Note:** results are probabilistic. TrustVision AI is a screening aid, not forensic proof. See [Limitations](#-limitations).

---

## ✨ Features

- 🔍 AI-powered deepfake detection
- 📷 Webcam image capture
- 🖼️ Image upload support
- 📊 Confidence and authenticity score visualization
- 🛡️ Risk assessment (LOW / MEDIUM / HIGH)
- 🔬 Metadata and forensic signal analysis
- 📄 PDF report generation
- 💾 Scan history storage
- ⚡ Fast REST API using FastAPI
- 🎨 Responsive React UI
- 🤖 Optional Gemini Vision verification

---

## 🏗️ Project Architecture

```text
                User
                 │
                 ▼
        React + Vite Frontend
                 │
          REST API Requests
                 │
                 ▼
          FastAPI Backend
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
 AI Inference Engine    SQLite Database
 (SigLIP model:         (Scan History)
  local PyTorch or
  remote inference)
      │
      ▼
 Prediction + Confidence
      │
      ▼
 PDF Report Generation
```

---

## 🛠️ Tech Stack

### Frontend
- React.js
- Vite
- Tailwind CSS
- JavaScript

### Backend
- FastAPI
- Python
- SQLAlchemy
- SQLite

### Artificial Intelligence
- PyTorch
- Hugging Face Transformers
- SigLIP deepfake detector ([`prithivMLmods/deepfake-detector-model-v1`](https://huggingface.co/prithivMLmods/deepfake-detector-model-v1))
- Google Gemini Vision (optional)

### Other Libraries
- ReportLab
- Pillow
- OpenCV
- NumPy

---

## 📂 Project Structure

```text
TrustVision-AI/
│
├── Frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── Backend/
│   ├── main.py
│   ├── reporting.py
│   └── requirements.txt
│
├── database/
│
├── ml/
│   ├── inference.py
│   ├── gemini_verifier.py
│   └── runtime_config.py
│
├── test_images/
│
├── app.py
├── start_app.py
├── requirements.txt
├── requirements-ml.txt
└── README.md
```

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/sushantsorigin/TrustVisionAI.git
cd TrustVisionAI
```

### 2. Install Backend Dependencies

Choose one:

```bash
# Lightweight API (uses remote inference, needs a Hugging Face token)
pip install -r requirements.txt

# Full local inference (PyTorch, OpenCV; downloads the model on first run)
pip install -r requirements-ml.txt
```

### 3. Install Frontend Dependencies

```bash
cd Frontend
npm install
cd ..
```

### 4. Run the Application

Start both services together:

```bash
python start_app.py
```

Or run them separately:

```bash
# Backend
python -m uvicorn Backend.main:app --reload

# Frontend (new terminal)
cd Frontend
npm run dev
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

---

## ⚙️ Configuration

Set these as environment variables (a `Backend/.env` file is loaded automatically and is git-ignored). Never commit API keys.

| Variable | Purpose |
|---|---|
| `TRUSTVISION_INFERENCE_BACKEND` | `local`, `remote` or `auto` |
| `HF_TOKEN` | Hugging Face token (remote inference) |
| `GEMINI_API_KEY` | Enables optional Gemini verification |
| `GEMINI_MODEL` | Gemini model name (set to a currently available model) |
| `CORS_ALLOW_ORIGINS` | Allowed frontend origins |
| `VITE_API_BASE_URL` | Frontend: backend URL when deployed separately |

---

## 💻 Usage

1. Open the application.
2. Upload an image or capture one using the webcam.
3. Wait for the AI model to process the image.
4. View:
   - Prediction (REAL / FAKE)
   - Confidence Score
   - Authenticity Score
   - Risk Level
5. Download the generated PDF report.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service and model status |
| `GET` | `/model-info` | Model metadata |
| `POST` | `/scan` | Analyze an image (multipart field `file`) |
| `GET` | `/reports/{id}` | Download the PDF report for a scan |

---

## 📊 Workflow

```text
Upload Image
      │
      ▼
Image Validation
      │
      ▼
AI Model Inference
      │
      ▼
Metadata + Forensic Analysis
      │
      ▼
Deepfake Prediction + Confidence
      │
      ▼
Risk Assessment
      │
      ▼
Save Scan + Generate PDF Report
```

---

## 🎯 Use Cases

- Digital media verification (as a first-pass screen)
- Social media content analysis
- Journalism and fact-checking support
- Cybersecurity awareness and education
- Educational research

---

## ⚠️ Limitations

- Results are probabilistic and can be wrong in both directions; do not rely on them as the sole basis for serious decisions.
- The model author reports about 94% accuracy on their own test split and labels the model experimental. Real-world accuracy may be lower.
- Designed for face images only; heatmaps are not supported.
- Remote inference depends on third-party free-tier quotas.
- No user authentication yet.

---

## 🔮 Future Improvements

- Video deepfake detection
- Real-time camera analysis
- Mobile application
- Self-hosted or in-browser inference
- Evaluation on a labeled benchmark (precision, recall, F1)
- Explainable AI (XAI)
- Face manipulation localization
- User authentication dashboard

---

## 📸 Screenshots

> Add screenshots of:
>
> - Home Page
> - Upload Page
> - Detection Result
> - PDF Report

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository.
2. Create a new feature branch.
3. Commit your changes.
4. Push to your branch.
5. Open a Pull Request.

---

## 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

**B SUSHANT**

Information Science Engineering Student

AI • Machine Learning • Full Stack Development • Computer Vision

---

### ⭐ If you found this project useful, please consider giving it a Star!
