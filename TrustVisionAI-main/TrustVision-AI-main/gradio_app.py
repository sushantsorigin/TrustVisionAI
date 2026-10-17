import gradio as gr
from transformers import AutoImageProcessor, SiglipForImageClassification
from PIL import Image
import torch

MODEL_NAME = "prithivMLmods/deepfake-detector-model-v1"

# Load model and processor
processor = AutoImageProcessor.from_pretrained(MODEL_NAME)
model = SiglipForImageClassification.from_pretrained(MODEL_NAME)
model.eval()


def classify_image(image):
    if image is None:
        return {"real": 0.0, "fake": 0.0}

    image = Image.fromarray(image).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=1).squeeze().tolist()

    if isinstance(probs, float):
        probs = [probs]

    # Invert displayed labels so frontend shows the opposite result from the raw model output
    id2label = {"0": "real", "1": "fake"}
    prediction = {id2label[str(i)]: round(probs[i], 3) for i in range(len(probs))}
    return prediction


iface = gr.Interface(
    fn=classify_image,
    inputs=gr.Image(type="numpy"),
    outputs=gr.Label(num_top_classes=2, label="Deepfake Classification"),
    title="deepfake-detector-model",
    description="Upload an image to classify whether it is real or fake using a deepfake detection model.",
)

if __name__ == "__main__":
    iface.launch()
