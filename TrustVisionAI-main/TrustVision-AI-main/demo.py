import argparse
import base64
from pathlib import Path

from ml.inference import DeepfakeDetector
from ml.runtime_config import GRADCAM_DIR


def _write_heatmap(heatmap_base64: str, image_path: Path) -> Path | None:
    if not heatmap_base64:
        return None

    payload = heatmap_base64.split(",", 1)[-1]
    output_path = GRADCAM_DIR / f"{image_path.stem}_heatmap.jpg"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(base64.b64decode(payload))
    return output_path


def infer_image(image_path: str):
    source = Path(image_path).expanduser().resolve()
    detector = DeepfakeDetector()
    result = detector.predict_image(source.read_bytes())

    if not result.get("success"):
        raise RuntimeError(result.get("error", "Inference failed."))

    heatmap_path = _write_heatmap(result.get("heatmap_base64"), source)

    print("=" * 50)
    print(f"Image            : {source.name}")
    print(f"Prediction       : {result['prediction']}")
    print(f"Authenticity     : {result['authenticity_score']:.2f}%")
    print(f"Confidence       : {result['confidence']:.2f}%")
    print(f"REAL probability : {result['real_probability']:.2f}%")
    print(f"FAKE probability : {result['fake_probability']:.2f}%")
    print(f"Model version    : {result['model_version']}")
    if heatmap_path is not None:
        print(f"Heatmap          : {heatmap_path}")
    print("=" * 50)

    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run a TrustVision image scan from the command line.')
    parser.add_argument('--image', required=True, help='Path to the image file')
    args = parser.parse_args()

    infer_image(args.image)
