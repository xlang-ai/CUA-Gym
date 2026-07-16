"""Image preprocessing helpers for the Qwen-VL WebEnv agent.

Implements a lightweight ``smart_resize`` compatible with Qwen-VL's vision
preprocessor (dimensions divisible by ``factor``, pixel count capped), plus
``process_image`` which returns a base64 PNG ready for multimodal chat APIs.
"""

from __future__ import annotations

import base64
import math
from io import BytesIO
from typing import Optional, Tuple, Union

import numpy as np
from PIL import Image

IMAGE_FACTOR = 32
MIN_PIXELS = 4 * 32 * 32
# Matches the OSWorld Qwen3.5-VL agent default: 16 * 16 * 4 * 12800
MAX_PIXELS = 16 * 16 * 4 * 12800
MAX_RATIO = 200


def round_by_factor(number: float, factor: int) -> int:
    return round(number / factor) * factor


def ceil_by_factor(number: float, factor: int) -> int:
    return math.ceil(number / factor) * factor


def floor_by_factor(number: float, factor: int) -> int:
    return math.floor(number / factor) * factor


def smart_resize(
    height: int,
    width: int,
    factor: int = IMAGE_FACTOR,
    min_pixels: Optional[int] = None,
    max_pixels: Optional[int] = None,
) -> Tuple[int, int]:
    """Rescale so both dims are divisible by ``factor`` and pixels stay in range."""
    min_pixels = MIN_PIXELS if min_pixels is None else min_pixels
    max_pixels = MAX_PIXELS if max_pixels is None else max_pixels
    if max(height, width) / max(min(height, width), 1) > MAX_RATIO:
        raise ValueError(
            f"absolute aspect ratio must be smaller than {MAX_RATIO}, "
            f"got {max(height, width) / min(height, width)}"
        )
    h_bar = max(factor, round_by_factor(height, factor))
    w_bar = max(factor, round_by_factor(width, factor))
    if h_bar * w_bar > max_pixels:
        beta = math.sqrt((height * width) / max_pixels)
        h_bar = floor_by_factor(height / beta, factor)
        w_bar = floor_by_factor(width / beta, factor)
    elif h_bar * w_bar < min_pixels:
        beta = math.sqrt(min_pixels / (height * width))
        h_bar = ceil_by_factor(height * beta, factor)
        w_bar = ceil_by_factor(width * beta, factor)
    return h_bar, w_bar


def to_png_bytes(image: Union[bytes, np.ndarray, Image.Image]) -> bytes:
    """Normalize a screenshot (bytes / ndarray / PIL) to PNG bytes."""
    if isinstance(image, bytes):
        return image
    if isinstance(image, np.ndarray):
        img = Image.fromarray(image.astype(np.uint8))
    elif isinstance(image, Image.Image):
        img = image
    else:
        raise TypeError(f"Unsupported screenshot type: {type(image)!r}")
    buf = BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()


def process_image(
    image: Union[bytes, np.ndarray, Image.Image],
    factor: int = IMAGE_FACTOR,
    max_pixels: int = MAX_PIXELS,
) -> Tuple[str, Tuple[int, int], Tuple[int, int]]:
    """Resize + re-encode a screenshot for the vision model.

    Returns:
        ``(base64_png, (original_w, original_h), (processed_w, processed_h))``
    """
    png_bytes = to_png_bytes(image)
    img = Image.open(BytesIO(png_bytes)).convert("RGB")
    original_width, original_height = img.size

    resized_height, resized_width = smart_resize(
        height=original_height,
        width=original_width,
        factor=factor,
        max_pixels=max_pixels,
    )
    img = img.resize((resized_width, resized_height))
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return b64, (original_width, original_height), (resized_width, resized_height)
