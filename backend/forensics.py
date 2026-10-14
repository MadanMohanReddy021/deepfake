
from io import BytesIO

import numpy as np
from PIL import (
    Image,
    ImageChops,
    ImageFilter,
    ExifTags,
)


def analyze_image_forensics(image, original_bytes):
    """
    Produce descriptive forensic indicators.

    These measurements are NOT a trained fake-image detector
    and must not be interpreted as proof of manipulation.
    """

    # Preserve the original image for metadata inspection.
    original = Image.open(BytesIO(original_bytes))
    metadata = extract_metadata(original)

    # Analyze pixel data in RGB format.
    rgb_image = image.convert("RGB")
    rgb = np.asarray(rgb_image, dtype=np.float32)

    grayscale = np.asarray(
        rgb_image.convert("L"),
        dtype=np.float32,
    )

    # --------------------------------------------------
    # 1. RGB AND GRAYSCALE HISTOGRAMS
    # --------------------------------------------------

    histogram_labels = [
        f"{i * 16}-{i * 16 + 15}"
        for i in range(16)
    ]

    histograms = {}

    for channel_index, channel_name in enumerate(
        ["red", "green", "blue"]
    ):
        counts, _ = np.histogram(
            rgb[:, :, channel_index],
            bins=16,
            range=(0, 256),
        )

        histograms[channel_name] = counts.tolist()

    gray_counts, _ = np.histogram(
        grayscale,
        bins=16,
        range=(0, 256),
    )

    histograms["grayscale"] = gray_counts.tolist()

    # Descriptive color statistics.
    color_statistics = {
        "red_mean": round(float(rgb[:, :, 0].mean()), 2),
        "green_mean": round(float(rgb[:, :, 1].mean()), 2),
        "blue_mean": round(float(rgb[:, :, 2].mean()), 2),
        "grayscale_mean": round(float(grayscale.mean()), 2),
        "grayscale_std": round(float(grayscale.std()), 2),
    }

    # --------------------------------------------------
    # 2. NOISE RESIDUAL ANALYSIS
    # --------------------------------------------------

    # Difference between the original image and a blurred copy.
    # This is a simple high-frequency residual, not a true
    # estimate of the camera sensor's noise.
    blurred = rgb_image.filter(
        ImageFilter.GaussianBlur(radius=1.0)
    )

    residual_image = ImageChops.difference(
        rgb_image,
        blurred,
    )

    residual = np.asarray(
        residual_image,
        dtype=np.float32,
    )

    noise_residual_mean = float(residual.mean())
    noise_residual_std = float(residual.std())

    # --------------------------------------------------
    # 3. EDGE ANALYSIS
    # --------------------------------------------------

    edges = rgb_image.convert("L").filter(
        ImageFilter.FIND_EDGES
    )

    edge_array = np.asarray(
        edges,
        dtype=np.float32,
    )

    # Percentage of pixels with relatively strong edges.
    edge_threshold = 40.0
    edge_density = float(
        np.mean(edge_array > edge_threshold) * 100
    )

    # --------------------------------------------------
    # 4. FREQUENCY-DOMAIN ANALYSIS
    # --------------------------------------------------

    # Downsample large images to reduce CPU and memory usage.
    frequency_image = rgb_image.convert("L").resize(
        (256, 256),
        Image.Resampling.LANCZOS,
    )

    frequency_array = np.asarray(
        frequency_image,
        dtype=np.float32,
    )

    spectrum = np.fft.fftshift(
        np.fft.fft2(frequency_array)
    )

    magnitude = np.abs(spectrum)

    # Ignore the low-frequency center and summarize the
    # remaining frequency energy.
    yy, xx = np.indices(magnitude.shape)
    center_y, center_x = 128, 128

    distance = np.sqrt(
        (yy - center_y) ** 2 +
        (xx - center_x) ** 2
    )

    high_frequency = magnitude[distance > 35]

    high_frequency_energy = float(
        np.mean(high_frequency)
    )

    # --------------------------------------------------
    # 5. JPEG COMPRESSION INFORMATION
    # --------------------------------------------------

    quantization_table_count = 0

    if original.format == "JPEG":
        quantization_tables = getattr(
            original,
            "quantization",
            None,
        )

        if quantization_tables:
            quantization_table_count = len(
                quantization_tables
            )

    return {
        "metadata": metadata,
        "histogram": {
            "labels": histogram_labels,
            "channels": histograms,
        },
        "color_statistics": color_statistics,
        "pixel_analysis": {
            "noise_residual_mean": round(
                noise_residual_mean, 3
            ),
            "noise_residual_std": round(
                noise_residual_std, 3
            ),
            "edge_density_percent": round(
                edge_density, 2
            ),
            "high_frequency_energy": round(
                high_frequency_energy, 3
            ),
            "jpeg_quantization_table_count":
                quantization_table_count,
        },
        "interpretation": (
            "These are descriptive image statistics, "
            "not proof of authenticity or manipulation."
        ),
    }


def extract_metadata(image):
    """Extract selected image metadata without exposing all EXIF."""

    exif_result = {}

    try:
        exif = image.getexif()

        for tag_id, value in exif.items():
            tag_name = ExifTags.TAGS.get(
                tag_id,
                str(tag_id),
            )

            if tag_name in {
                "Make",
                "Model",
                "Software",
                "DateTime",
                "DateTimeOriginal",
                "DateTimeDigitized",
                "Orientation",
                "Artist",
                "Copyright",
            }:
                # Avoid returning arbitrary binary or huge values.
                if isinstance(value, bytes):
                    value = value.decode(
                        "utf-8",
                        errors="replace",
                    )

                exif_result[tag_name] = str(value)[:300]

    except Exception:
        exif_result = {}

    return {
        "format": image.format or "Unknown",
        "width": image.width,
        "height": image.height,
        "mode": image.mode,
        "exif_found": bool(exif_result),
        "exif": exif_result,
        "note": (
            "Missing metadata does not mean an image is fake. "
            "Metadata can be removed or modified."
        ),
    }
