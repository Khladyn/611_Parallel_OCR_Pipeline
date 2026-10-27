"""
Pipeline coordinator.
Sets up shared queue, locks, counter, spawns workers, and tracks runtime metrics.
"""

import os
import csv
import time
import queue
import threading
import multiprocessing
from typing import Dict, Any
from pipeline.workers import loader_worker, processing_worker


def run_pipeline(config: Dict[str, Any]) -> Dict[str, Any]:
    """Coordinates lifecycle of loader and processing workers."""
    image_dir = config.get("image_dir", "dataset")
    n_workers = int(config.get("n_workers", 2))
    output_file = config.get("output_file", "ocr_results.csv")
    backend = config.get("backend", "process")

    # Initialize CSV header
    out_dir = os.path.dirname(output_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["ID", "image_filename", "extracted_text", "processing_time_ms"])

    print("=" * 55)
    print("PARALLEL OCR PIPELINE")
    print(f"  Dataset Directory : {image_dir}")
    print(f"  Processing Workers: {n_workers} (+ 1 loader)")
    print(f"  Mode              : {backend.upper()}")
    print("=" * 55)

    t0 = time.perf_counter()

    if backend == "process":
        # Multiprocessing primitives
        img_queue = multiprocessing.Queue(maxsize=300)
        csv_lock = multiprocessing.Lock()
        id_counter = multiprocessing.Value("i", 1)

        loader = multiprocessing.Process(
            target=loader_worker,
            args=(image_dir, img_queue, n_workers)
        )
        workers = [
            multiprocessing.Process(
                target=processing_worker,
                args=(i + 1, img_queue, output_file, csv_lock, id_counter)
            )
            for i in range(n_workers)
        ]
    else:
        # Threading primitives
        img_queue = queue.Queue(maxsize=300)
        csv_lock = threading.Lock()
        id_counter = [1]

        loader = threading.Thread(
            target=loader_worker,
            args=(image_dir, img_queue, n_workers)
        )
        workers = [
            threading.Thread(
                target=processing_worker,
                args=(i + 1, img_queue, output_file, csv_lock, id_counter)
            )
            for i in range(n_workers)
        ]

    # Start loader and workers
    loader.start()
    for w in workers:
        w.start()

    # Wait for completion
    loader.join()
    for w in workers:
        w.join()

    total_time = round(time.perf_counter() - t0, 4)
    total_imgs = (id_counter.value - 1) if backend == "process" else (id_counter[0] - 1)
    throughput = round(total_imgs / total_time, 2) if total_time > 0 else 0.0

    print("-" * 55)
    print(f"Images Processed : {total_imgs}")
    print(f"Execution Time   : {total_time:.4f} s")
    print(f"Throughput       : {throughput} images/sec")
    print(f"Output File      : {output_file}")
    print("=" * 55)

    return {
        "n_workers": n_workers,
        "total_images": total_imgs,
        "total_time_sec": total_time,
        "throughput_ips": throughput,
        "output_file": output_file
    }
