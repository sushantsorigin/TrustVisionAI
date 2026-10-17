"""
Deployment-safe deepfake inference wrapper.

Local development can use the Hugging Face SigLip model through PyTorch.
Vercel deployments default to the Hugging Face Inference API so the serverless
bundle does not need to include local torch/transformers/OpenCV wheels.
"""

import io
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / "Backend" / ".env")

try:
    from PIL import ExifTags, Image
except ImportError:
    ExifTags = None
    Image = None

_BACKEND_ENV = os.getenv("TRUSTVISION_INFERENCE_BACKEND", "auto").strip().lower()
_REMOTE_ONLY = _BACKEND_ENV == "remote" or (_BACKEND_ENV in {"", "auto"} and os.getenv("VERCEL"))

if _REMOTE_ONLY:
    cv2 = None
    np = None
    dct = None
    torch = None
    AutoImageProcessor = None
    SiglipForImageClassification = None
    mp = None
else:
    try:
        import cv2
    except ImportError:
        cv2 = None

    try:
        import numpy as np
    except ImportError:
        np = None

    try:
        from scipy.fftpack import dct
    except ImportError:
        dct = None

    try:
        import torch
        from transformers import AutoImageProcessor, SiglipForImageClassification
    except ImportError:
        torch = None
        AutoImageProcessor = None
        SiglipForImageClassification = None

    try:
        import mediapipe as mp
    except ImportError:
        mp = None

from .runtime_config import LABEL_MAPPING_NOTE, MODEL_NAME, MODEL_VERSION


MEDIAPIPE_AVAILABLE = mp is not None
LOCAL_ML_AVAILABLE = all(
    dependency is not None
    for dependency in (
        cv2,
        np,
        Image,
        dct,
        torch,
        AutoImageProcessor,
        SiglipForImageClassification,
    )
)


class DeepfakeDetector:
    """
    Wraps the TrustVision detection backend.

    Backend selection:
      - TRUSTVISION_INFERENCE_BACKEND=local uses local torch/transformers.
      - TRUSTVISION_INFERENCE_BACKEND=remote uses Hugging Face Inference API.
      - auto (default) uses remote on Vercel and local when local ML deps exist.
    """

    def __init__(self, model_name: str = None):
        self.model_name = model_name or MODEL_NAME
        self.class_map = {"REAL": 1, "FAKE": 0}
        self.model_loaded = False
        self.load_error = None
        self.processor = None
        self.model = None
        self.face_cascade = None
        self.mp_face_mesh = None
        self.hf_token = (
            os.getenv("HF_TOKEN")
            or os.getenv("HUGGINGFACEHUB_API_TOKEN")
            or os.getenv("HUGGING_FACE_HUB_TOKEN")
            or ""
        )
        self.remote_endpoint = os.getenv(
            "HF_INFERENCE_URL",
            f"https://router.huggingface.co/hf-inference/models/{self.model_name}",
        )

        requested_backend = os.getenv("TRUSTVISION_INFERENCE_BACKEND", "auto").strip().lower()
        if requested_backend not in {"auto", "local", "remote"}:
            requested_backend = "auto"

        if requested_backend == "remote" or (requested_backend == "auto" and os.getenv("VERCEL")):
            self.backend = "remote"
            self.model_loaded = True
            print(f"[DeepfakeDetector] Using remote Hugging Face Inference API: {self.remote_endpoint}")
        elif requested_backend == "local" or LOCAL_ML_AVAILABLE:
            self.backend = "local"
            self._init_local_model()
        else:
            self.backend = "remote"
            self.model_loaded = True
            self.load_error = "Local ML dependencies are not installed; using remote inference."
            print(f"[DeepfakeDetector] {self.load_error}")

    def _init_local_model(self):
        if not LOCAL_ML_AVAILABLE:
            self.load_error = (
                "Local inference dependencies are missing. Install requirements-ml.txt "
                "or set TRUSTVISION_INFERENCE_BACKEND=remote."
            )
            print(f"[DeepfakeDetector] {self.load_error}")
            return

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        try:
            self.processor = AutoImageProcessor.from_pretrained(self.model_name)
            self.model = SiglipForImageClassification.from_pretrained(self.model_name).to(self.device)
            self.model.eval()

            id2label = getattr(self.model.config, "id2label", None)
            if id2label:
                normalized = {int(k): str(v).strip().upper() for k, v in id2label.items()}
                real_idx = next((i for i, label in normalized.items() if label == "REAL"), None)
                fake_idx = next((i for i, label in normalized.items() if label == "FAKE"), None)
                if real_idx is not None and fake_idx is not None:
                    self.class_map = {"REAL": real_idx, "FAKE": fake_idx}

            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self.face_cascade = cv2.CascadeClassifier(cascade_path)

            self.mp_face_mesh = (
                mp.solutions.face_mesh.FaceMesh(
                    static_image_mode=True,
                    max_num_faces=1,
                    refine_landmarks=True,
                )
                if MEDIAPIPE_AVAILABLE
                else None
            )

            self.model_loaded = True
            print(
                f"[DeepfakeDetector] Loaded '{self.model_name}' on {self.device} "
                f"| class_map={self.class_map}"
            )
        except Exception as exc:
            self.load_error = str(exc)
            print(f"[DeepfakeDetector] ERROR: Failed to load HF model '{self.model_name}': {exc}")

    def metadata(self) -> dict:
        return {
            "model_loaded": self.model_loaded,
            "model_name": self.model_name,
            "model_version": MODEL_VERSION,
            "inference_backend": self.backend,
            "device": str(getattr(self, "device", "remote")),
            "class_map": self.class_map,
            "label_mapping_note": LABEL_MAPPING_NOTE,
            "local_ml_available": LOCAL_ML_AVAILABLE,
            "mediapipe_available": MEDIAPIPE_AVAILABLE,
            "remote_endpoint": self.remote_endpoint if self.backend == "remote" else None,
            "remote_auth_configured": bool(self.hf_token),
            "load_error": self.load_error,
        }

    def predict_image(self, image_bytes: bytes) -> dict:
        try:
            if not self.model_loaded:
                raise RuntimeError(
                    f"Model not loaded ('{self.model_name}'). Error: {self.load_error}"
                )

            if self.backend == "remote":
                return self._predict_image_remote(image_bytes)
            return self._predict_image_local(image_bytes)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def _predict_image_remote(self, image_bytes: bytes) -> dict:
        remote_scores = self._run_remote_model(image_bytes)
        metadata_signals = self._read_metadata_signals(image_bytes)
        forensic_signals = self._default_forensic_signals("Remote Vercel inference skips local OpenCV analysis.")

        fusion = self._fuse_probabilities(
            remote_scores["REAL"],
            remote_scores["FAKE"],
            metadata_signals,
            forensic_signals,
        )

        real_prob = fusion["real_probability"]
        fake_prob = fusion["fake_probability"]
        prediction = "REAL" if real_prob >= fake_prob else "FAKE"
        confidence = max(real_prob, fake_prob) * 100
        risk_level = self._risk_level(prediction, confidence, fake_prob, metadata_signals, forensic_signals)

        return {
            "success": True,
            "prediction": prediction,
            "authenticity_score": round(real_prob * 100, 3),
            "confidence": round(confidence, 2),
            "risk_level": risk_level,
            "real_probability": round(real_prob * 100, 3),
            "fake_probability": round(fake_prob * 100, 3),
            "neural_real_probability": round(remote_scores["REAL"] * 100, 3),
            "neural_fake_probability": round(remote_scores["FAKE"] * 100, 3),
            "model_version": f"{MODEL_VERSION} via Hugging Face Inference API",
            "inference_backend": "remote",
            "class_map": self.class_map,
            "heatmap_base64": None,
            "heatmap_error": "Heatmap generation is not supported in remote Vercel inference mode.",
            "face_box": self._full_image_box(image_bytes),
            "forensic_analysis": {
                "metadata": metadata_signals,
                "signals": forensic_signals,
                "forensic_adjustment": fusion["forensic_adjustment"],
                "fusion_reasons": fusion["fusion_reasons"],
            },
        }

    def _predict_image_local(self, image_bytes: bytes) -> dict:
        np_img = np.frombuffer(image_bytes, np.uint8)
        img_bgr = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise ValueError("Could not decode image. Ensure the file is a valid image.")

        face_img, face_box = self._detect_face(img_bgr)
        if face_img is None:
            face_img = img_bgr
            face_box = (0, 0, img_bgr.shape[1], img_bgr.shape[0])

        face_pil = Image.fromarray(cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB))
        full_pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))

        face_probs = self._run_model(face_pil)
        full_probs = self._run_model(full_pil)
        blended = (0.6 * face_probs) + (0.4 * full_probs)

        real_idx = self.class_map["REAL"]
        fake_idx = self.class_map["FAKE"]
        neural_real = float(blended[real_idx].item())
        neural_fake = float(blended[fake_idx].item())

        metadata_signals = self._read_metadata_signals(image_bytes)
        forensic_signals = self._compute_forensic_signals(face_img)
        fusion = self._fuse_probabilities(neural_real, neural_fake, metadata_signals, forensic_signals)

        real_prob = fusion["real_probability"]
        fake_prob = fusion["fake_probability"]
        prediction = "REAL" if real_prob >= fake_prob else "FAKE"
        confidence = max(real_prob, fake_prob) * 100
        risk_level = self._risk_level(prediction, confidence, fake_prob, metadata_signals, forensic_signals)

        return {
            "success": True,
            "prediction": prediction,
            "authenticity_score": round(real_prob * 100, 3),
            "confidence": round(confidence, 2),
            "risk_level": risk_level,
            "real_probability": round(real_prob * 100, 3),
            "fake_probability": round(fake_prob * 100, 3),
            "neural_real_probability": round(neural_real * 100, 3),
            "neural_fake_probability": round(neural_fake * 100, 3),
            "model_version": MODEL_VERSION,
            "inference_backend": "local",
            "class_map": self.class_map,
            "heatmap_base64": None,
            "heatmap_error": "Heatmap generation is not supported for the SigLip model.",
            "face_box": {
                "x1": face_box[0],
                "y1": face_box[1],
                "x2": face_box[2],
                "y2": face_box[3],
            },
            "forensic_analysis": {
                "metadata": metadata_signals,
                "signals": forensic_signals,
                "forensic_adjustment": fusion["forensic_adjustment"],
                "fusion_reasons": fusion["fusion_reasons"],
            },
        }

    def _run_remote_model(self, image_bytes: bytes) -> dict:
        headers = {"Content-Type": "application/octet-stream"}
        if self.hf_token:
            headers["Authorization"] = f"Bearer {self.hf_token}"

        timeout = int(os.getenv("HF_INFERENCE_TIMEOUT", "45"))
        request = urllib.request.Request(
            self.remote_endpoint,
            data=image_bytes,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                raise RuntimeError(
                    "Hugging Face rejected HF_TOKEN (401). Verify that the token is valid "
                    "and has permission to use Inference Providers, then restart the backend."
                ) from exc
            if exc.code == 403:
                raise RuntimeError(
                    "Hugging Face denied inference access (403). Verify that HF_TOKEN has "
                    "permission to use Inference Providers."
                ) from exc
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Hugging Face inference failed ({exc.code}): {body}") from exc

        if isinstance(payload, dict) and payload.get("error"):
            raise RuntimeError(f"Hugging Face inference error: {payload['error']}")
        if isinstance(payload, list) and len(payload) == 1 and isinstance(payload[0], list):
            payload = payload[0]
        if not isinstance(payload, list):
            raise RuntimeError(f"Unexpected Hugging Face response: {payload}")

        scores = {"REAL": 0.0, "FAKE": 0.0}
        for item in payload:
            label = str(item.get("label", "")).strip().upper()
            score = float(item.get("score", 0.0))
            if label in {"REAL", "LABEL_1"}:
                scores["REAL"] = score
            elif label in {"FAKE", "LABEL_0"}:
                scores["FAKE"] = score

        total = scores["REAL"] + scores["FAKE"]
        if total <= 0:
            raise RuntimeError(f"Could not map Hugging Face labels from response: {payload}")

        return {
            "REAL": scores["REAL"] / total,
            "FAKE": scores["FAKE"] / total,
        }

    def predict_video(self, video_path: str, fps_sample_rate: int = 1) -> dict:
        if self.backend != "local":
            return {
                "success": False,
                "error": "Video scanning requires local ML dependencies and is not enabled on Vercel.",
            }

        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Could not open video file: {video_path}")

            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            frame_step = max(1, int(fps / fps_sample_rate))

            scores, confidences, fake_probs = [], [], []
            frame_idx = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_idx % frame_step == 0:
                    ok, buf = cv2.imencode(".jpg", frame)
                    if ok:
                        result = self.predict_image(buf.tobytes())
                        if result.get("success"):
                            scores.append(result["authenticity_score"])
                            confidences.append(result["confidence"])
                            fake_probs.append(result["fake_probability"] / 100.0)
                frame_idx += 1

            cap.release()

            if not scores:
                raise ValueError("No frames could be processed from the video.")

            avg_score = sum(scores) / len(scores)
            avg_conf = sum(confidences) / len(confidences)
            avg_fake = sum(fake_probs) / len(fake_probs)
            prediction = "FAKE" if avg_fake > 0.5 else "REAL"

            if prediction == "FAKE" and avg_conf > 80:
                risk = "HIGH"
            elif prediction == "FAKE" or avg_conf < 70:
                risk = "MEDIUM"
            else:
                risk = "LOW"

            return {
                "success": True,
                "prediction": prediction,
                "authenticity_score": round(avg_score, 2),
                "confidence": round(avg_conf, 2),
                "risk_level": risk,
                "total_frames_analyzed": len(scores),
                "heatmap_base64_thumbnail": None,
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def _run_model(self, pil_img):
        inputs = self.processor(images=pil_img.convert("RGB"), return_tensors="pt").to(self.device)
        with torch.no_grad():
            logits = self.model(**inputs).logits
            probs = torch.nn.functional.softmax(logits, dim=1)[0]
        return probs

    def _detect_face(self, img_bgr):
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
        if len(faces) == 0:
            return None, None

        x, y, w, h = max(faces, key=lambda rect: rect[2] * rect[3])
        mx, my = int(w * 0.2), int(h * 0.2)
        x1 = max(0, x - mx)
        y1 = max(0, y - my)
        x2 = min(img_bgr.shape[1], x + w + mx)
        y2 = min(img_bgr.shape[0], y + h + my)
        return img_bgr[y1:y2, x1:x2], (x1, y1, x2, y2)

    def _read_metadata_signals(self, image_bytes: bytes) -> dict:
        signals = {
            "is_ai_metadata": False,
            "has_camera_exif": False,
            "ai_metadata_hits": [],
            "camera_exif_tags": [],
            "editor_metadata_hits": [],
            "metadata_error": None,
        }
        if Image is None or ExifTags is None:
            signals["metadata_error"] = "Pillow is not installed."
            return signals

        ai_terms = (
            "midjourney",
            "stable diffusion",
            "stable-diffusion",
            "dall-e",
            "dalle",
            "ai generated",
            "aigc",
            "comfyui",
            "automatic1111",
            "novelai",
            "invokeai",
            "sdxl",
            "flux",
            "firefly",
            "generative ai",
            "openai",
            "chatgpt",
        )
        editor_terms = ("photoshop", "lightroom", "gimp", "snapseed")
        camera_tag_names = {
            "Make",
            "Model",
            "LensModel",
            "LensMake",
            "ExposureTime",
            "FNumber",
            "ISOSpeedRatings",
            "PhotographicSensitivity",
            "FocalLength",
            "DateTimeOriginal",
        }

        try:
            with Image.open(io.BytesIO(image_bytes)) as pil_raw:
                info_text = " ".join(f"{key}={value}" for key, value in pil_raw.info.items()).lower()
                signals["ai_metadata_hits"] = [term for term in ai_terms if term in info_text]
                signals["editor_metadata_hits"] = [term for term in editor_terms if term in info_text]
                signals["is_ai_metadata"] = bool(signals["ai_metadata_hits"])

                exif = pil_raw.getexif()
                if exif:
                    for key in exif:
                        tag = str(ExifTags.TAGS.get(key, key))
                        if tag in camera_tag_names:
                            signals["camera_exif_tags"].append(tag)
                    signals["has_camera_exif"] = bool(signals["camera_exif_tags"])
        except Exception as exc:
            signals["metadata_error"] = str(exc)

        return signals

    def _full_image_box(self, image_bytes: bytes) -> dict:
        if Image is None:
            return {"x1": 0, "y1": 0, "x2": 0, "y2": 0}
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                width, height = img.size
            return {"x1": 0, "y1": 0, "x2": width, "y2": height}
        except Exception:
            return {"x1": 0, "y1": 0, "x2": 0, "y2": 0}

    def _default_forensic_signals(self, note: str) -> dict:
        return {
            "analysis_mode": note,
            "laplacian_variance": None,
            "dct_high_frequency_ratio": None,
            "edge_fraction": None,
            "ela_variance": None,
            "strong_flags": {
                "very_low_texture": False,
                "very_low_edge_density": False,
                "very_low_high_frequency_energy": False,
                "high_ela_variance": False,
            },
            "weak_flags": {
                "low_texture": False,
                "low_edge_density": False,
                "low_high_frequency_energy": False,
                "medium_ela_variance": False,
            },
            "strong_signal_count": 0,
            "weak_signal_count": 0,
        }

    def _compute_forensic_signals(self, face_img) -> dict:
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        gray_f = gray.astype(np.float32)

        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        hf_ratio = float(self._dct_high_freq_ratio(gray_f))
        edges = cv2.Canny(gray, 100, 200)
        edge_fraction = float(np.mean(edges > 0))
        ela_variance = float(self._ela_variance(face_img))

        strong_flags = {
            "very_low_texture": laplacian_var < 30.0,
            "very_low_edge_density": edge_fraction < 0.0025,
            "very_low_high_frequency_energy": hf_ratio < 5e-6,
            "high_ela_variance": ela_variance > 100.0,
        }
        weak_flags = {
            "low_texture": laplacian_var < 60.0,
            "low_edge_density": edge_fraction < 0.006,
            "low_high_frequency_energy": hf_ratio < 1e-5,
            "medium_ela_variance": ela_variance > 50.0,
        }

        return {
            "laplacian_variance": round(laplacian_var, 6),
            "dct_high_frequency_ratio": round(hf_ratio, 10),
            "edge_fraction": round(edge_fraction, 6),
            "ela_variance": round(ela_variance, 6),
            "strong_flags": strong_flags,
            "weak_flags": weak_flags,
            "strong_signal_count": int(sum(strong_flags.values())),
            "weak_signal_count": int(sum(weak_flags.values())),
        }

    def _dct_high_freq_ratio(self, gray_f) -> float:
        dct_y = dct(dct(gray_f.T, norm="ortho").T, norm="ortho")
        power = np.abs(dct_y) ** 2
        h, w = power.shape
        high = np.sum(power[int(h * 0.5):, int(w * 0.5):])
        total = np.sum(power)
        return high / total if total > 0 else 0.0

    def _ela_variance(self, face_img) -> float:
        _, enc = cv2.imencode(".jpg", face_img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        dec = cv2.imdecode(enc, cv2.IMREAD_COLOR)
        diff = cv2.absdiff(face_img.astype(np.float32), dec.astype(np.float32))
        return float(np.var(diff))

    def _fuse_probabilities(
        self,
        neural_real: float,
        neural_fake: float,
        metadata_signals: dict,
        forensic_signals: dict,
    ) -> dict:
        fake_prob = float(self._clip(neural_fake, 0.001, 0.999))
        adjustment = 0.0
        reasons = []

        strong = forensic_signals["strong_flags"]
        weak = forensic_signals["weak_flags"]
        strong_count = forensic_signals["strong_signal_count"]

        if metadata_signals["is_ai_metadata"]:
            adjustment += 0.75
            reasons.append("explicit AI-generation metadata detected")

        if strong["very_low_texture"]:
            adjustment += 0.10
            reasons.append("very low facial texture variance")
        elif weak["low_texture"]:
            adjustment += 0.02

        if strong["very_low_edge_density"]:
            adjustment += 0.08
            reasons.append("very low edge density")
        elif weak["low_edge_density"]:
            adjustment += 0.02

        if strong["very_low_high_frequency_energy"]:
            adjustment += 0.06
            reasons.append("very low high-frequency DCT energy")
        elif weak["low_high_frequency_energy"]:
            adjustment += 0.01

        if strong["high_ela_variance"]:
            adjustment += 0.08
            reasons.append("high ELA variance")
        elif weak["medium_ela_variance"]:
            adjustment += 0.02

        if not metadata_signals["has_camera_exif"] and strong_count >= 1:
            adjustment += 0.04
            reasons.append("no camera EXIF with synthetic artifact signals")

        fused_fake = min(0.99, fake_prob + adjustment)
        if metadata_signals["is_ai_metadata"]:
            fused_fake = max(fused_fake, 0.97)
        elif not metadata_signals["has_camera_exif"] and strong_count >= 3:
            fused_fake = max(fused_fake, 0.72)
        elif not metadata_signals["has_camera_exif"] and strong_count >= 2:
            fused_fake = max(fused_fake, 0.62)

        fused_real = 1.0 - fused_fake
        return {
            "real_probability": fused_real,
            "fake_probability": fused_fake,
            "forensic_adjustment": round(fused_fake - fake_prob, 6),
            "fusion_reasons": reasons,
        }

    def _risk_level(
        self,
        prediction: str,
        confidence: float,
        fake_probability: float,
        metadata_signals: dict,
        forensic_signals: dict,
    ) -> str:
        if prediction == "FAKE":
            if metadata_signals["is_ai_metadata"] or fake_probability >= 0.85:
                return "HIGH"
            return "MEDIUM"
        if confidence < 65 or forensic_signals["strong_signal_count"] >= 2:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _clip(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))
