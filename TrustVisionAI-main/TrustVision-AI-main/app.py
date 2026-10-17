import os
from tempfile import gettempdir


if os.getenv("VERCEL"):
    tmp_dir = gettempdir()
    os.environ.setdefault("TRUSTVISION_INFERENCE_BACKEND", "remote")
    os.environ.setdefault("HF_HOME", os.path.join(tmp_dir, "huggingface"))
    os.environ.setdefault("HF_HUB_CACHE", os.path.join(tmp_dir, "huggingface", "hub"))
    os.environ.setdefault("TRANSFORMERS_CACHE", os.path.join(tmp_dir, "huggingface", "transformers"))


from Backend.main import app
