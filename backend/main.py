
from io import BytesIO
from .forensics import analyze_image_forensics
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
from transformers import pipeline
from .forensic_findings import interpret_forensic_results
from .heatmap import generate_attention_heatmap
import os
import tempfile
from pathlib import Path

from fastapi import File, HTTPException, UploadFile

from .video_analysis import analyze_video_path

app = FastAPI(title="VERITY AI Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Loading VERITY model...")

detector = pipeline(
    "image-classification",
    model="Wvolf/ViT_Deepfake_Detection",
    device=-1,
)

print("VERITY model ready!")


@app.get("/")
def home():
    return {"message": "VERITY API is running"}


@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):

    # Validate image format
    if file.content_type not in {
        "image/jpeg",
        "image/png",
        "image/webp",
    }:
        raise HTTPException(
            status_code=415,
            detail="Upload a JPG, PNG, or WebP image.",
        )

    # Read uploaded file
    contents = await file.read()

    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Image must be under 10 MB.",
        )

    # Open and validate image
    try:
        image = Image.open(BytesIO(contents))
        image.load()
        image = image.convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=400,
            detail="Invalid image file.",
        )

    # Run deepfake classification
    try:
        results = detector(image)
    except Exception as error:
        print("Model prediction failed:", error)
        raise HTTPException(
            status_code=500,
            detail="Image classification failed.",
        )

    # Generate attention heatmap
    heatmap_base64 = None

    try:
        heatmap_base64 = generate_attention_heatmap(
            image,
            detector,
        )
    except Exception as error:
        print("Heatmap generation failed:", error)

    # Convert model outputs into percentage scores
    scores = {
        item["label"].lower(): round(
            float(item["score"]) * 100, 2
        )
        for item in results
    }

    fake_score = next(
        (
            score
            for label, score in scores.items()
            if "fake" in label or "deepfake" in label
        ),
        None,
    )

    real_score = next(
        (
            score
            for label, score in scores.items()
            if "real" in label or "genuine" in label
        ),
        None,
    )

    # Check expected model labels
    if fake_score is None or real_score is None:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Unexpected model labels.",
                "labels": list(scores.keys()),
            },
        )

    prediction = (
        "Potentially manipulated"
        if fake_score > real_score
        else "Likely authentic"
    )
    forensic_results = None

    try:
        forensic_results = analyze_image_forensics(
           image,
        contents,
    )
    except Exception as error:
       print("Forensic analysis failed:", error)
    if forensic_results is not None:
        forensic_results["interpretation"] = (
            interpret_forensic_results(forensic_results)
        )
    return {
        "filename": file.filename,
        "prediction": prediction,
        "fake_score": fake_score,
        "real_score": real_score,
        "heatmap": heatmap_base64,
        "forensics": forensic_results,
        "warning": (
            "Model prediction only; this is not proof "
            "of authenticity."
        ),
    }

VIDEO_MAX_SIZE = 100 * 1024 * 1024

ALLOWED_VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".avi", ".mkv", ".webm"
}


@app.post("/analyze-video")
async def analyze_video(file: UploadFile = File(...)):
    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Upload an MP4, MOV, AVI, MKV, or WebM video.",
        )

    contents = await file.read(VIDEO_MAX_SIZE + 1)

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="The uploaded video is empty.",
        )

    if len(contents) > VIDEO_MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Video size must not exceed 100 MB.",
        )

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temporary_file:
            temporary_file.write(contents)
            temporary_path = Path(temporary_file.name)

        # IMPORTANT:
        # Replace `classifier` below with the variable name
        # of your EXISTING Hugging Face pipeline in main.py.
        result = analyze_video_path(
            temporary_path,
            detector,
        )

        result["filename"] = file.filename

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        print("Video analysis failed:", repr(exc))

        raise HTTPException(
            status_code=500,
            detail="Video analysis failed. Check the backend terminal.",
        ) from exc

    finally:
        await file.close()

        if temporary_path and temporary_path.exists():
            os.remove(temporary_path)
