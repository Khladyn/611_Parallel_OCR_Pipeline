# Worker functions for the Producer-Consumer pipeline
# Loader enqueues image file paths, while Workers preprocess, run OCR, and append results to CSV

import os
import time
import csv
from typing import Any
from pipeline.preprocessing import preprocess_image
from pipeline.ocr_engine import extract_text

VALID_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}


# Producer: scans directory or takes list and puts image paths into the shared queue
def loader_worker(image_source: Any, queue: Any, n_workers: int) -> None:
    if isinstance(image_source, (list, tuple)):
        files = list(image_source)
    elif isinstance(image_source, str) and os.path.isdir(image_source):
        files = [
            os.path.join(image_source, f) for f in sorted(os.listdir(image_source))
            if os.path.splitext(f)[1].lower() in VALID_EXTENSIONS
        ]
    else:
        print(f"[Loader] Image source '{image_source}' not found or invalid.")
        for _ in range(n_workers):
            queue.put(None)
        return

    for f in files:
        queue.put(f)

    # Send a poison pill (None) for each worker to shut them down cleanly when finished
    for _ in range(n_workers):
        queue.put(None)


# Consumer: pulls images from queue, runs preprocessing and OCR, and writes to CSV
def processing_worker(
    worker_id: int,
    queue: Any,
    csv_path: str,
    lock: Any,
    counter: Any
) -> None:
    while True:
        try:
            image_path = queue.get()
        except Exception:
            break

        # Check if we got a poison pill (sentinel value)
        if image_path is None:
            break

        filename = os.path.basename(image_path)
        try:
            t0 = time.perf_counter()

            # Preprocessing and OCR inference (done in RAM)
            prep_img = preprocess_image(image_path)
            text = extract_text(prep_img)

            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

            # Critical section: mutex lock protects atomic ID increments and CSV writes
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
