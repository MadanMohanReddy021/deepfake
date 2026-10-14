
from transformers import pipeline
from PIL import Image

MODEL_NAME = "Wvolf/ViT_Deepfake_Detection"

print("Loading VERITY deepfake detector...")
print("The first run downloads the model. Please wait.")

detector = pipeline(
    "image-classification",
    model=MODEL_NAME,
    device=-1
)

print("Model loaded successfully!")

image_path = input("Enter the path to a face image: ").strip().strip('"')

try:
    image = Image.open(image_path).convert("RGB")
    results = detector(image)

    print("\n--- VERITY ANALYSIS ---")

    for result in results:
        label = result["label"]
        score = result["score"] * 100

        print(f"{label}: {score:.2f}%")

    print("\nAnalysis complete.")
    print("These are model scores, not proof of authenticity.")

except FileNotFoundError:
    print("Error: Image file not found. Check the path.")

except Exception as error:
    print(f"Analysis failed: {error}")
