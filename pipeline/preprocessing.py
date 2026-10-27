"""
Image preprocessing for OCR.
Applies grayscale conversion, denoising, contrast enhancement, and Otsu binarization.
"""

from PIL import Image, ImageEnhance, ImageFilter
import numpy as np


def otsu_threshold(gray_arr: np.ndarray) -> int:
    """Computes optimal binarization threshold using vectorized Otsu's method."""
    hist = np.bincount(gray_arr.ravel(), minlength=256)
    total = gray_arr.size
    sum_total = np.dot(np.arange(256), hist)

    weight_bg = np.cumsum(hist)
    weight_fg = total - weight_bg
    sum_bg = np.cumsum(np.arange(256) * hist)

    # Filter out empty background or foreground to avoid divide-by-zero
    valid = (weight_bg > 0) & (weight_fg > 0)
    if not np.any(valid):
        return 128

    mean_bg = sum_bg[valid] / weight_bg[valid]
    mean_fg = (sum_total - sum_bg[valid]) / weight_fg[valid]

    # Maximize between-class variance
    var_between = weight_bg[valid] * weight_fg[valid] * ((mean_bg - mean_fg) ** 2)
    thresholds = np.arange(256)[valid]

    return int(thresholds[np.argmax(var_between)])


def preprocess_image(image_path: str, binarize: bool = True) -> Image.Image:
    """Preprocesses image to maximize OCR text recognition accuracy."""
    with Image.open(image_path) as img:
        # Convert RGBA/palette to RGB, then to Grayscale
        gray = img.convert("RGB").convert("L")

    # Denoise with 3x3 median filter
    denoised = gray.filter(ImageFilter.MedianFilter(size=3))

    # Enhance contrast
    enhanced = ImageEnhance.Contrast(denoised).enhance(1.5)

    if not binarize:
        return enhanced

    # Fast Otsu binarization
    arr = np.array(enhanced, dtype=np.uint8)
    thresh = otsu_threshold(arr)
    bin_arr = np.where(arr > thresh, 255, 0).astype(np.uint8)

    return Image.fromarray(bin_arr)
