
import cv2
import numpy as np

from PIL import Image


MAX_FRAMES = 8


def get_class_scores(classifier, image):
    """
    Run the existing Hugging Face image-classification pipeline
    on one RGB PIL image.
    """
    predictions = classifier(image, top_k=None)

    if predictions and isinstance(predictions[0], list):
        predictions = predictions[0]

    real_score = None
    fake_score = None

    for item in predictions:
        label = str(item.get("label", "")).strip().lower()
        score = float(item.get("score", 0.0))

        if any(word in label for word in (
            "fake", "deepfake", "synthetic", "manipulated"
        )):
            fake_score = score * 100

        elif any(word in label for word in (
            "real", "authentic", "original", "genuine"
        )):
            real_score = score * 100

    if real_score is None or fake_score is None:
        labels = [item.get("label") for item in predictions]
        raise ValueError(
            "Could not identify the model's real/fake labels. "
            f"Model returned: {labels}"
        )

    return real_score, fake_score


def analyze_video_path(video_path, classifier):
    """
    Sample frames across the video and analyze each with the
    existing image deepfake classifier.
    """
    capture = cv2.VideoCapture(str(video_path))

    if not capture.isOpened():
        raise ValueError(
            "Unable to open this video. Try a supported MP4 video."
        )

    try:
        total_frames = int(
            capture.get(cv2.CAP_PROP_FRAME_COUNT)
        )
        fps = float(capture.get(cv2.CAP_PROP_FPS))

        if total_frames <= 0:
            raise ValueError("The video contains no readable frames.")

        if fps <= 0:
            raise ValueError("Could not determine the video frame rate.")

        duration = total_frames / fps

        if duration <= 0:
            raise ValueError("Invalid video duration.")

        frame_count = min(MAX_FRAMES, total_frames)

        # Spread samples across the video rather than analyzing
        # only the beginning.
        positions = np.linspace(
            0,
            total_frames - 1,
            num=frame_count,
            dtype=int,
        )

        frame_results = []

        for frame_number in positions:
            capture.set(cv2.CAP_PROP_POS_FRAMES, int(frame_number))
            success, frame = capture.read()

            if not success:
                continue

            timestamp = float(frame_number / fps)

            # Reduce very large frames to help CPU inference.
            height, width = frame.shape[:2]
            scale = min(1.0, 512 / max(height, width))

            if scale < 1.0:
                frame = cv2.resize(
                    frame,
                    (
                        max(1, int(width * scale)),
                        max(1, int(height * scale)),
                    ),
                    interpolation=cv2.INTER_AREA,
                )

            rgb_frame = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB,
            )

            pil_image = Image.fromarray(rgb_frame)

            real_score, fake_score = get_class_scores(
                classifier,
                pil_image,
            )

            prediction = (
                "Fake"
                if fake_score > real_score
                else "Real"
            )

            frame_results.append({
                "frame_number": int(frame_number),
                "timestamp_seconds": round(timestamp, 2),
                "prediction": prediction,
                "real_score": round(real_score, 2),
                "fake_score": round(fake_score, 2),
            })

        if not frame_results:
            raise ValueError(
                "No frames could be extracted from this video."
            )

        average_real = sum(
            item["real_score"] for item in frame_results
        ) / len(frame_results)

        average_fake = sum(
            item["fake_score"] for item in frame_results
        ) / len(frame_results)

        fake_frames = sum(
            item["prediction"] == "Fake"
            for item in frame_results
        )

        real_frames = len(frame_results) - fake_frames

        overall_prediction = (
            "Potentially manipulated"
            if average_fake > average_real
            else "More consistent with real"
        )

        return {
            "filename": video_path.name,
            "duration_seconds": round(duration, 2),
            "total_video_frames": total_frames,
            "frames_analyzed": len(frame_results),
            "prediction": overall_prediction,
            "average_real_score": round(average_real, 2),
            "average_fake_score": round(average_fake, 2),
            "fake_frames": fake_frames,
            "real_frames": real_frames,
            "frame_results": frame_results,
            "method": "Sampled-frame image classification",
            "warning": (
                "This is a preliminary frame-based assessment. "
                "It does not analyze temporal inconsistencies or "
                "guarantee video authenticity."
            ),
        }

    finally:
        capture.release()
