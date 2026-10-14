
from transformers import AutoModel, AutoImageProcessor

MODEL_NAME = "Wvolf/ViT_Deepfake_Detection"

print("Loading model architecture...")

processor = AutoImageProcessor.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)

print("\nModel type:", type(model).__name__)
print("Configuration:", model.config.model_type)
print("Image size:", getattr(model.config, "image_size", "unknown"))
print("Patch size:", getattr(model.config, "patch_size", "unknown"))

print("\nAttention-related modules:")
for name, module in model.named_modules():
    if "attention" in name.lower() and name.count(".") <= 3:
        print(name, "->", type(module).__name__)

print("\nInspection complete.")
