
def interpret_forensic_results(forensics):
    """Explain measured findings without claiming proof of forgery."""

    metadata = forensics["metadata"]
    pixels = forensics["pixel_analysis"]
    colors = forensics["color_statistics"]

    findings = []

    # Metadata
    if metadata["exif_found"]:
        fields = list(metadata["exif"].keys())

        findings.append({
            "category": "Metadata",
            "title": "EXIF metadata detected",
            "observation": (
                "Recognized fields: " + ", ".join(fields)
            ),
            "interpretation": (
                "These fields provide contextual information "
                "about the image. They can be edited or copied, "
                "so their presence does not prove authenticity."
            ),
            "evidence_level": "Contextual only",
        })
    else:
        findings.append({
            "category": "Metadata",
            "title": "No recognized EXIF metadata",
            "observation": (
                "No recognized EXIF fields were extracted."
            ),
            "interpretation": (
                "Metadata may have been stripped during export, "
                "editing, screenshot capture, or sharing. "
                "This is not proof of manipulation."
            ),
            "evidence_level": "Weak / inconclusive",
        })

    # Color statistics
    findings.append({
        "category": "Color analysis",
        "title": "RGB intensity distribution measured",
        "observation": (
            f"Mean intensities — red: {colors['red_mean']}, "
            f"green: {colors['green_mean']}, "
            f"blue: {colors['blue_mean']}."
        ),
        "interpretation": (
            "These values describe the image's color balance. "
            "Differences can result from lighting, scene content, "
            "white balance, or editing. They do not independently "
            "indicate whether the image is fake."
        ),
        "evidence_level": "Descriptive only",
    })

    # Noise residual
    findings.append({
        "category": "Pixel analysis",
        "title": "High-frequency residual measured",
        "observation": (
            f"Residual mean: {pixels['noise_residual_mean']}; "
            f"residual standard deviation: "
            f"{pixels['noise_residual_std']}."
        ),
        "interpretation": (
            "The residual measures differences between the image "
            "and a blurred version. Fine texture, sharpening, "
            "compression, and noise can all affect it. A suspicious "
            "finding requires validated reference ranges and "
            "appropriate comparison."
        ),
        "evidence_level": "Descriptive only",
    })

    # Edge analysis
    findings.append({
        "category": "Pixel analysis",
        "title": "Edge density measured",
        "observation": (
            f"{pixels['edge_density_percent']}% of pixels "
            "exceeded the configured edge threshold."
        ),
        "interpretation": (
            "Edges can reflect object boundaries, hair, texture, "
            "and image sharpness. This global measurement does not "
            "identify manipulated regions."
        ),
        "evidence_level": "Descriptive only",
    })

    # Frequency analysis
    findings.append({
        "category": "Frequency analysis",
        "title": "High-frequency energy measured",
        "observation": (
            "Mean high-frequency spectrum magnitude: "
            f"{pixels['high_frequency_energy']}."
        ),
        "interpretation": (
            "This summarizes selected spatial-frequency content. "
            "Its meaning depends on image resolution, resizing, "
            "compression, and scene detail. No authenticity "
            "conclusion is justified without validated comparisons."
        ),
        "evidence_level": "Descriptive only",
    })

    # JPEG information
    if metadata["format"] == "JPEG":
        findings.append({
            "category": "Compression",
            "title": "JPEG compression information inspected",
            "observation": (
                "Quantization tables found: "
                f"{pixels['jpeg_quantization_table_count']}."
            ),
            "interpretation": (
                "Quantization tables describe aspects of JPEG "
                "compression. Their count alone cannot establish "
                "whether an image was edited or manipulated."
            ),
            "evidence_level": "Contextual only",
        })
    else:
        findings.append({
            "category": "Compression",
            "title": "JPEG-specific analysis not applicable",
            "observation": (
                f"Input format: {metadata['format']}."
            ),
            "interpretation": (
                "JPEG quantization-table analysis does not apply "
                "directly to this input format."
            ),
            "evidence_level": "Not applicable",
        })

    return {
        "findings": findings,
        "conclusion": (
            "The forensic measurements are descriptive indicators, "
            "not proof of authenticity or manipulation. Interpret "
            "them alongside the AI result and independently "
            "validated evidence."
        ),
    }
