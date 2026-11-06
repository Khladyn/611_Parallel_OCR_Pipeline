# Pipeline coordinator and concurrency manager
# Sets up the shared FIFO queue, locks, counter, spawns workers, and tracks runtime stats

import os
import csv
import time
import queue
import threading
import multiprocessing
from typing import Dict, Any, List
from pipeline.preprocessing import preprocess_image
from pipeline.workers import loader_worker, processing_worker


# Runs the entire pipeline using either processes or threads
def run_pipeline(config: Dict[str, Any]) -> Dict[str, Any]:
    image_dir = config.get("image_dir", "dataset")
    n_workers = int(config.get("n_workers", 2))
    output_file = config.get("output_file", "ocr_results.csv")
    backend = config.get("backend", "process")

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
        # Multiprocessing: separate processes bypass Python's GIL
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
        # Threading: threads share Python's memory space and GIL
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

    # Start the producer loader and all consumer workers
    loader.start()
    for w in workers:
        w.start()

    # Wait for all workers to finish their jobs
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


# Helper worker chunk processor for the in-Python CPU benchmarking
def _process_cpu_chunk(paths: List[str]) -> None:
    for p in paths:
        _ = preprocess_image(p)


# Runs the in-Python CPU preprocessing pipeline across workers (used for pure GIL scaling benchmarks)
def run_cpu_benchmark(image_paths: List[str], n_workers: int, backend: str = "process") -> Dict[str, Any]:
    chunks = [image_paths[i::n_workers] for i in range(n_workers)]
    t0 = time.perf_counter()

    if backend == "process":
        workers = [
            multiprocessing.Process(target=_process_cpu_chunk, args=(c,))
            for c in chunks
        ]
    else:
        workers = [
            threading.Thread(target=_process_cpu_chunk, args=(c,))
            for c in chunks
        ]

    for w in workers:
        w.start()
    for w in workers:
        w.join()
    if backend == "process":
        for w in workers:
            w.close()

    total_time = round(time.perf_counter() - t0, 4)
    total_imgs = len(image_paths)
    throughput = round(total_imgs / total_time, 2) if total_time > 0 else 0.0

    return {
        "n_workers": n_workers,
        "total_images": total_imgs,
        "total_time_sec": total_time,
        "throughput_ips": throughput,
        "backend": backend
    }
