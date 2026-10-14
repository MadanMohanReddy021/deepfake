
import base64
from io import BytesIO

import numpy as np
import torch
from PIL import Image
from matplotlib import colormaps


def generate_attention_heatmap(image, detector):
    """
    Generate an approximate ViT attention-rollout visualization.

    This visualizes attention patterns, not proof of manipulation.
    """

    model = detector.model
    processor = detector.image_processor
    device = next(model.parameters()).device

    attention_maps = []
    handles = []

    def capture_attention(module, inputs):
        if not inputs or not torch.is_tensor(inputs[0]):
            return

        hidden_states = inputs[0]

        if hidden_states.ndim != 3:
            return

        if not hasattr(module, "q_proj") or not hasattr(module, "k_proj"):
            return

        with torch.no_grad():
            query = module.q_proj(hidden_states)
            key = module.k_proj(hidden_states)

            heads = getattr(
                module,
                "num_heads",
                getattr(
                    module,
                    "num_attention_heads",
                    getattr(model.config, "num_attention_heads", None),
                ),
            )

            if heads is None or query.shape[-1] % heads != 0:
                return

            batch, tokens, hidden = query.shape
            head_dim = hidden // heads

            query = query.reshape(
                batch, tokens, heads, head_dim
            ).transpose(1, 2)

            key = key.reshape(
                batch, tokens, heads, head_dim
            ).transpose(1, 2)

            scores = torch.matmul(
                query, key.transpose(-2, -1)
            ) / (head_dim ** 0.5)

            attention = torch.softmax(scores, dim=-1)

            # Average the attention across heads.
            attention_maps.append(
                attention.mean(dim=1)[0].detach().cpu()
            )

    # Register hooks on every compatible attention layer.
    for _, module in model.named_modules():
        if (
            hasattr(module, "q_proj")
            and hasattr(module, "k_proj")
            and hasattr(module, "o_proj")
        ):
            handles.append(
                module.register_forward_pre_hook(capture_attention)
            )

    try:
        inputs = processor(
            images=image,
            return_tensors="pt",
        )

        inputs = {
            key: value.to(device)
            for key, value in inputs.items()
        }

        with torch.no_grad():
            model(**inputs)

    finally:
        for handle in handles:
            handle.remove()

    if not attention_maps:
        raise RuntimeError(
            "Could not capture attention maps from this model."
        )

    # Attention rollout with residual connections.
    token_count = attention_maps[0].shape[-1]

    rollout = torch.eye(token_count)

    for attention in attention_maps:
        attention = attention.float()

        # Approximate the residual connection.
        attention = attention + torch.eye(token_count)
        attention = attention / attention.sum(
            dim=-1, keepdim=True
        ).clamp_min(1e-8)

        rollout = attention @ rollout

    # Determine whether the model uses a class token.
    side_with_cls = int(np.sqrt(token_count - 1))
    side_without_cls = int(np.sqrt(token_count))

    if side_with_cls * side_with_cls == token_count - 1:
        patch_scores = rollout[0, 1:]
        grid_size = side_with_cls
    elif side_without_cls * side_without_cls == token_count:
        patch_scores = rollout.mean(dim=0)
        grid_size = side_without_cls
    else:
        raise RuntimeError(
            f"Cannot infer patch grid from {token_count} tokens."
        )

    heatmap = patch_scores.reshape(
        grid_size, grid_size
    ).numpy()

    # Normalize the attention values for visualization.
    heatmap = heatmap - heatmap.min()
    heatmap = heatmap / max(float(heatmap.max()), 1e-8)

    # Resize the patch map to the uploaded image dimensions.
    heatmap_image = Image.fromarray(
        np.uint8(heatmap * 255)
    ).resize(image.size, Image.Resampling.BILINEAR)

    heatmap_array = np.asarray(heatmap_image) / 255.0
    color_array = colormaps["jet"](heatmap_array)[..., :3]

    original_array = np.asarray(
        image.convert("RGB")
    ).astype(np.float32) / 255.0

    # Overlay the heatmap on the original image.
    overlay = (
        0.55 * original_array + 0.45 * color_array
    )

    overlay_image = Image.fromarray(
        np.uint8(np.clip(overlay, 0, 1) * 255)
    )

    buffer = BytesIO()
    overlay_image.save(buffer, format="PNG")

    return base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")
