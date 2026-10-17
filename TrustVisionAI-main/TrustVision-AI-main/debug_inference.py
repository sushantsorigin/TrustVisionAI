"""
TrustVision AI inference debugger.

Run:
    python debug_inference.py --image path/to/image.jpg
"""
import argparse
from pathlib import Path

from ml.inference import DeepfakeDetector


def _print_section(title):
    print("\n" + "=" * 64)
    print(title)
    print("=" * 64)


def run(image_path):
    source = Path(image_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Image not found: {source}")

    detector = DeepfakeDetector()
    result = detector.predict_image(source.read_bytes())

    _print_section("Model")
    metadata = detector.metadata()
    print(f"Loaded:       {metadata['model_loaded']}")
    print(f"Path:         {metadata['model_path']}")
    print(f"Version:      {metadata['model_version']}")
    print(f"Device:       {metadata['device']}")
    print(f"Class map:    {metadata['class_map']} ({metadata['class_map_source']})")
    print(f"Label source: {metadata.get('checkpoint_label_source') or 'unknown'}")

    _print_section("Result")
    if not result.get("success"):
        print(f"ERROR: {result.get('error', 'Inference failed')}")
        return result

    print(f"Image:             {source.name}")
    print(f"Prediction:        {result['prediction']}")
    print(f"Authenticity:      {result['authenticity_score']:.2f}%")
    print(f"Confidence:        {result['confidence']:.2f}%")
    print(f"Risk:              {result['risk_level']}")
    print(f"REAL probability:  {result['real_probability']:.2f}%")
    print(f"FAKE probability:  {result['fake_probability']:.2f}%")
    print(f"NN REAL raw:       {result['neural_real_probability']:.2f}%")
    print(f"NN FAKE raw:       {result['neural_fake_probability']:.2f}%")

    forensic = result.get("forensic_analysis", {})
    metadata_signals = forensic.get("metadata", {})
    signals = forensic.get("signals", {})

    _print_section("Metadata Signals")
    print(f"Camera EXIF present: {metadata_signals.get('has_camera_exif')}")
    print(f"Camera EXIF tags:    {metadata_signals.get('camera_exif_tags') or []}")
    print(f"AI metadata present: {metadata_signals.get('is_ai_metadata')}")
    print(f"AI metadata hits:    {metadata_signals.get('ai_metadata_hits') or []}")
    print(f"Editor metadata:     {metadata_signals.get('editor_metadata_hits') or []}")
    if metadata_signals.get("metadata_error"):
        print(f"Metadata error:      {metadata_signals['metadata_error']}")

    _print_section("Forensic Signals")
    print(f"Laplacian variance:       {signals.get('laplacian_variance')}")
    print(f"DCT high-frequency ratio: {signals.get('dct_high_frequency_ratio')}")
    print(f"Edge fraction:            {signals.get('edge_fraction')}")
    print(f"Strong signal count:      {signals.get('strong_signal_count')}")
    print(f"Weak signal count:        {signals.get('weak_signal_count')}")
    print(f"Strong flags:             {signals.get('strong_flags')}")
    print(f"Weak flags:               {signals.get('weak_flags')}")
    print(f"Fake adjustment:          {forensic.get('forensic_adjustment')}")
    print(f"Fusion reasons:           {forensic.get('fusion_reasons') or []}")

    if result.get("heatmap_error"):
        print(f"\nHeatmap warning: {result['heatmap_error']}")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnose a TrustVision image scan.")
    parser.add_argument("--image", required=True, help="Path to the image to diagnose.")
    args = parser.parse_args()
    run(args.image)
