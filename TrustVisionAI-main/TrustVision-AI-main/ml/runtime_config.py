"""
Runtime configuration for TrustVision AI.

The system uses the Hugging Face SigLip model exclusively:
  prithivMLmods/deepfake-detector-model-v1

Label space (from model config):
  id2label = {0: "fake", 1: "real"}
"""

# Hugging Face model identifier
MODEL_NAME = "prithivMLmods/deepfake-detector-model-v1"

# Human-readable version string shown in API responses and PDF reports
MODEL_VERSION = "SigLip Deepfake Detector v1 (HuggingFace)"

# Informational note included in /model-info responses
LABEL_MAPPING_NOTE = (
    "Inference uses the pre-trained Hugging Face SigLip model "
    "'prithivMLmods/deepfake-detector-model-v1' with label mapping: "
    "class 0 = FAKE, class 1 = REAL."
)
