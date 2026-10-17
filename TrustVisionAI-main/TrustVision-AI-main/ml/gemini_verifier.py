"""
Optional Gemini Vision verifier.

The local PyTorch detector remains the primary path. Gemini is used only when a
GEMINI_API_KEY, GEMINI_API_KEYS, or GOOGLE_API_KEY environment variable is set.
"""
import json
import os
import re

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
_QUOTA_ERRORS = ("quota", "rate", "limit", "429", "resource exhausted", "exceeded", "too many")

_PROMPT = """You are an expert forensic image analyst.

Analyse this image and decide if it is:
- REAL: a genuine photograph taken by a camera
- AI_GENERATED: fully created by AI, such as Midjourney, DALL-E, Stable Diffusion, Firefly, FLUX, or similar
- DEEPFAKE: a real photo with a face/body synthetically replaced or manipulated

Use visual forensic evidence, not vibes: unnatural geometry, inconsistent fine texture, hair/teeth/ear artifacts, background inconsistencies, lighting conflicts, and metadata-like generation signs if visible.

Respond only with valid JSON:
{"verdict":"REAL","confidence":85,"reasoning":"One or two sentence explanation."}"""


def _load_api_keys():
    raw = (
        os.getenv("GEMINI_API_KEYS")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or ""
    )
    return [key.strip() for key in re.split(r"[,;\s]+", raw) if key.strip()]


class GeminiVerifier:
    def __init__(self):
        self._api_keys = _load_api_keys()
        self._current_key_idx = 0
        self.enabled = False
        self.error = None
        self._client = None

        if not GEMINI_AVAILABLE:
            self.error = "google-genai not installed. Run: pip install google-genai"
            print(f"[GeminiVerifier] {self.error}")
            return

        if not self._api_keys:
            self.error = "Gemini disabled. Set GEMINI_API_KEY or GEMINI_API_KEYS to enable it."
            print(f"[GeminiVerifier] {self.error}")
            return

        self._try_init(self._current_key_idx)

    def _try_init(self, idx: int) -> bool:
        if idx >= len(self._api_keys):
            self.error = "All Gemini API keys exhausted or invalid."
            self.enabled = False
            return False
        try:
            self._client = genai.Client(api_key=self._api_keys[idx])
            self._current_key_idx = idx
            self.enabled = True
            self.error = None
            print(f"[GeminiVerifier] Ready with key #{idx + 1}/{len(self._api_keys)} ({_MODEL_NAME})")
            return True
        except Exception as exc:
            print(f"[GeminiVerifier] Key #{idx + 1} init error: {exc}")
            return self._try_init(idx + 1)

    def _rotate_key(self) -> bool:
        next_idx = self._current_key_idx + 1
        print(f"[GeminiVerifier] Quota hit on key #{self._current_key_idx + 1}. Trying key #{next_idx + 1}.")
        return self._try_init(next_idx)

    def verify(self, image_bytes: bytes) -> dict:
        empty = {
            "enabled": self.enabled,
            "verdict": None,
            "is_fake": None,
            "confidence": None,
            "reasoning": None,
            "error": self.error,
        }

        if not self.enabled or self._client is None:
            return empty

        mime = "image/jpeg"
        if image_bytes[:4] == b"\x89PNG":
            mime = "image/png"
        elif image_bytes[:6] in (b"GIF87a", b"GIF89a"):
            mime = "image/gif"
        elif image_bytes[:4] == b"RIFF":
            mime = "image/webp"

        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime)

        for _attempt in range(len(self._api_keys)):
            try:
                response = self._client.models.generate_content(
                    model=_MODEL_NAME,
                    contents=[_PROMPT, image_part],
                )
                raw = (response.text or "").strip()
                raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()
                match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
                parsed = json.loads(match.group(0) if match else raw)

                verdict = str(parsed.get("verdict", "UNKNOWN")).upper()
                confidence = int(parsed.get("confidence", 50))
                confidence = max(0, min(100, confidence))
                reasoning = str(parsed.get("reasoning", ""))
                is_fake = verdict in {"AI_GENERATED", "DEEPFAKE"}

                print(f"[GeminiVerifier] {verdict} ({confidence}%) - {reasoning[:80]}")
                return {
                    "enabled": True,
                    "verdict": verdict,
                    "is_fake": is_fake,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "error": None,
                }

            except Exception as exc:
                err_str = str(exc).lower()
                if any(keyword in err_str for keyword in _QUOTA_ERRORS):
                    if not self._rotate_key():
                        break
                    continue
                print(f"[GeminiVerifier] Error: {exc}")
                return {**empty, "enabled": True, "error": str(exc)}

        return {**empty, "enabled": False, "error": "All Gemini API keys are exhausted."}


_verifier: "GeminiVerifier | None" = None


def get_verifier() -> GeminiVerifier:
    global _verifier
    if _verifier is None:
        _verifier = GeminiVerifier()
    return _verifier
