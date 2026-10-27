"""
Worker processes for parallel OCR.
Loader enqueues images; workers preprocess, extract text, and append to CSV under a lock.
"""

import os
import time
import csv
from typing import Any
from pipeline.preprocessing import preprocess_image
from pipeline.ocr_engine import extract_text

VALID_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}


def loader_worker(image_dir: str, queue: Any, n_workers: int) -> None:
    """Producer: scans image_dir, pushes file paths into queue, then sends sentinels."""
    if not os.path.isdir(image_dir):
        print(f"[Loader] Directory '{image_dir}' not found.")
        for _ in range(n_workers):
            queue.put(None)
        return

    # Find valid images
    files = sorted([
        f for f in os.listdir(image_dir)
        if os.path.splitext(f)[1].lower() in VALID_EXTENSIONS
    ])

    print(f"[Loader] Enqueueing {len(files)} images from '{image_dir}'...")
    for f in files:
        queue.put(os.path.join(image_dir, f))

    # Send poison pills (None) to terminate each worker cleanly
    for _ in range(n_workers):
        queue.put(None)


def processing_worker(
    worker_id: int,
    queue: Any,
    csv_path: str,
    lock: Any,
    counter: Any
) -> None:
    """Consumer: takes images from queue, runs preprocessing + OCR, safely writes to CSV."""
    while True:
        try:
            image_path = queue.get()
        except Exception:
            break

        # Check termination sentinel
        if image_path is None:
            break

        filename = os.path.basename(image_path)
        try:
            t0 = time.perf_counter()

            # Preprocessing and OCR inference
            prep_img = preprocess_image(image_path)
            text = extract_text(prep_img)

            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

            # Critical section: synchronized sequential ID and CSV append
            with lock:
                if hasattr(counter, "value"):
                    row_id = counter.value
                    counter.value += 1
                else:
                    row_id = counter[0]
                    counter[0] += 1

                with open(csv_path, "a", newline="", encoding="utf-8") as f:
                    csv.writer(f).writerow([row_id, filename, text, elapsed_ms])

        except Exception as e:
            print(f"[Worker {worker_id}] Error processing {filename}: {e}")
