# Image preprocessing for OCR
# Cleans and prepares images through a 4-step pipeline:
# 1. Grayscale, 2. 3x3 Median Filter, 3. Contrast Boost, 4. Otsu Binarization

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


# Finds the optimal threshold using Otsu's method
def otsu_threshold(gray_arr: np.ndarray) -> int:
    # Build a 256-bin histogram of pixel brightness
    hist = np.bincount(gray_arr.ravel(), minlength=256)
    total = gray_arr.size
    sum_total = np.dot(np.arange(256), hist)

    weight_bg = np.cumsum(hist)
    weight_fg = total - weight_bg
    sum_bg = np.cumsum(np.arange(256) * hist)

    # Avoid dividing by zero if background or foreground is empty
    valid = (weight_bg > 0) & (weight_fg > 0)
    if not np.any(valid):
        return 128

    mean_bg = sum_bg[valid] / weight_bg[valid]
    mean_fg = (sum_total - sum_bg[valid]) / weight_fg[valid]

    # Maximize between-class variance between text ink and paper
    var_between = weight_bg[valid] * weight_fg[valid] * ((mean_bg - mean_fg) ** 2)
    thresholds = np.arange(256)[valid]

    return int(thresholds[np.argmax(var_between)])


# Runs the 4-step preprocessing on an image entirely in memory
def preprocess_image(image_path: str, binarize: bool = True) -> Image.Image:
    with Image.open(image_path) as img:
        # Step 1: Convert color channels into 2D grayscale luminance
        gray = img.convert("RGB").convert("L")

    # Step 2: Denoise with 3x3 median filter to remove scanner specks without blurring text edges
    denoised = gray.filter(ImageFilter.MedianFilter(size=3))

    # Step 3: Boost contrast by 1.5x so faint characters stand out from background
    enhanced = ImageEnhance.Contrast(denoised).enhance(1.5)

    if not binarize:
        return enhanced

    # Step 4: Otsu binarization converts grays into pure 0 (ink) and 255 (paper)
    arr = np.array(enhanced, dtype=np.uint8)
    thresh = otsu_threshold(arr)
    bin_arr = np.where(arr > thresh, 255, 0).astype(np.uint8)

    return Image.fromarray(bin_arr)
