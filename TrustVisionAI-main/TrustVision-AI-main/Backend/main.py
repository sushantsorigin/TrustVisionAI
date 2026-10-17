"""
TrustVision AI — FastAPI backend.

Endpoints:
  GET  /              — welcome message
  GET  /health        — model + Gemini status
  GET  /model-info    — full model metadata
  POST /scan          — deepfake detection on an uploaded image
  GET  /reports/{id}  — download PDF report for a past scan

The detector backend is initialized once at startup (global `detector`).
"""

import os
import sys

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session

# Allow imports from the project root (ml/, database/)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import models
from database.database import SessionLocal, engine
from ml.gemini_verifier import get_verifier
from ml.inference import DeepfakeDetector
from ml.runtime_config import MODEL_VERSION
from Backend.reporting import generate_pdf_report

# Create DB tables on startup if they don't exist
models.Base.metadata.create_all(bind=engine)

# Initialize the detector backend and optional Gemini verifier once at startup
detector = DeepfakeDetector()
gemini = get_verifier()

app = FastAPI(
    title="TrustVision AI",
    description="Enterprise Media Authenticity Platform — powered by SigLip deepfake detection",
    version="2.0.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
    if origin.strip()
]
allow_credentials = "*" not in allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Database dependency
# ---------------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def read_root():
    return {"message": "Welcome to TrustVision AI API"}


@app.get("/health")
def health_check():
    meta = detector.metadata()
    return {
        "status": "healthy" if meta["model_loaded"] else "degraded",
        "model_loaded": meta["model_loaded"],
        "model_name": meta["model_name"],
        "model_version": meta["model_version"],
        "inference_backend": meta.get("inference_backend"),
        "device": meta["device"],
        "gemini_enabled": gemini.enabled,
        "load_error": meta.get("load_error"),
    }


@app.get("/model-info")
def model_info():
    return detector.metadata()


@app.post("/scan")
async def scan_media(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Accept an uploaded image, run deepfake detection, persist the result,
    and return the full prediction payload to the frontend.

    Flow:
      1. Validate file type (images only).
      2. Run HF SigLip inference via DeepfakeDetector.predict_image().
      3. Optionally override with Gemini Vision if a key is configured.
      4. Persist the scan record to SQLite.
      5. Return JSON with scores, probabilities, forensic analysis, and report URL.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only image files are supported. Please upload a JPG, PNG, or WEBP file.",
        )

    try:
        image_bytes = await file.read()

        # --- Step 1: Primary inference (HF SigLip) ---
        result = detector.predict_image(image_bytes)
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Inference error: {result.get('error')}",
            )

        # --- Step 2: Optional Gemini Vision secondary verification ---
        gemini_result = gemini.verify(image_bytes)
        gemini_verdict = None

        if gemini_result["enabled"] and gemini_result["verdict"] and not gemini_result["error"]:
            gemini_verdict = gemini_result["verdict"]
            gemini_conf = float(gemini_result.get("confidence") or 0)

            # Gemini confident it's fake (≥75%) → override to FAKE
            if gemini_result["is_fake"] and gemini_conf >= 75:
                result["prediction"] = "FAKE"
                result["risk_level"] = "HIGH"
                result["confidence"] = max(result["confidence"], gemini_conf)
                result["authenticity_score"] = round(min(result["authenticity_score"], 30.0), 3)
                result["real_probability"] = min(
                    result.get("real_probability", 100.0), result["authenticity_score"]
                )
                result["fake_probability"] = max(
                    result.get("fake_probability", 0.0), 100.0 - result["authenticity_score"]
                )

            # Gemini very confident it's real (≥85%) but model says FAKE → override to REAL
            elif (
                not gemini_result["is_fake"]
                and result["prediction"] == "FAKE"
                and gemini_conf >= 85
            ):
                result["prediction"] = "REAL"
                result["risk_level"] = "LOW"
                result["confidence"] = max(result["confidence"], gemini_conf)
                result["authenticity_score"] = round(max(result["authenticity_score"], 70.0), 3)
                result["real_probability"] = max(
                    result.get("real_probability", 0.0), result["authenticity_score"]
                )
                result["fake_probability"] = min(
                    result.get("fake_probability", 100.0), 100.0 - result["authenticity_score"]
                )

        # --- Step 3: Invert prediction (model labels are swapped relative to display) ---
        if result.get("prediction") == "REAL":
            result["prediction"] = "FAKE"
        elif result.get("prediction") == "FAKE":
            result["prediction"] = "REAL"

        if result.get("real_probability") is not None and result.get("fake_probability") is not None:
            result["real_probability"], result["fake_probability"] = (
                result["fake_probability"],
                result["real_probability"],
            )
            result["authenticity_score"] = round(result["real_probability"], 3)
            result["confidence"] = max(result["real_probability"], result["fake_probability"])

        # --- Step 4: Persist scan record ---
        scan_record = models.ScanResult(
            filename=file.filename,
            authenticity_score=result["authenticity_score"],
            prediction=result["prediction"],
            confidence=result["confidence"],
            risk_level=result["risk_level"],
            user_id=1,  # Auth not yet wired; default to user 1
        )
        db.add(scan_record)
        db.commit()
        db.refresh(scan_record)

        # --- Step 5: Return response ---
        return {
            "id": scan_record.id,
            "filename": scan_record.filename,
            "authenticity_score": scan_record.authenticity_score,
            "prediction": scan_record.prediction,
            "confidence": scan_record.confidence,
            "risk_level": scan_record.risk_level,
            "timestamp": scan_record.timestamp.isoformat() if scan_record.timestamp else None,
            "real_probability": result.get("real_probability"),
            "fake_probability": result.get("fake_probability"),
            "model_version": result.get("model_version", MODEL_VERSION),
            "class_map": result.get("class_map"),
            "forensic_analysis": result.get("forensic_analysis"),
            "report_url": f"/reports/{scan_record.id}",
            "heatmap_base64": result.get("heatmap_base64"),
            "heatmap_error": result.get("heatmap_error"),
            "gemini_verdict": gemini_verdict,
            "gemini_reasoning": gemini_result.get("reasoning") if gemini_result["enabled"] else None,
            "gemini_confidence": gemini_result.get("confidence") if gemini_result["enabled"] else None,
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/reports/{scan_id}")
def download_report(scan_id: int, db: Session = Depends(get_db)):
    """Generate and stream a PDF report for a completed scan."""
    scan_record = db.query(models.ScanResult).filter(models.ScanResult.id == scan_id).first()
    if scan_record is None:
        raise HTTPException(status_code=404, detail=f"Scan #{scan_id} not found.")

    try:
        pdf_bytes, report_filename, _ = generate_pdf_report(scan_record)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{report_filename}"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}")
