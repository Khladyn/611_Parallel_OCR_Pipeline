# CSC611M Machine Project 1: Parallel OCR Pipeline
**Software Technology Department — De La Salle University**

---

## 1. Overview

Parallel OCR pipeline using Python standard library concurrency (`multiprocessing` / `threading`).
- **Loader Worker**: Scans `dataset/` and pushes images into a shared queue.
- **Processing Workers**: Pull images, preprocess, extract text, and append results to `ocr_results.csv`.
- **Synchronization**: Mutual exclusion lock protects CSV writing and atomic sequential IDs.
- **Model**: Integrates `eng.traineddata` for Tesseract with fallback to native Vision OCR.

---

## 2. Project Structure

```
611_Parallel_OCR_Pipeline/
├── config.txt                          # Configuration (image_dir & n_workers)
├── main.py                             # Main entry point
├── eng.traineddata                     # Tesseract English trained model
├── dataset/                            # 100 test images (img0001.png - img0100.png)
├── requirements.txt                    # Project dependencies
├── ocr_results.csv                     # Output results
├── benchmark.py                        # Speedup benchmark runner
├── benchmark_results.csv               # Benchmark measurements
├── benchmark_speedup.png               # Performance charts
├── generate_presentation.py            # Slide deck generator
├── Parallel_OCR_Pipeline_Report.pptx   # PowerPoint presentation
├── CSC611M_MP1_Parallel_OCR_Pipeline.zip # Submission zip archive
└── pipeline/
    ├── __init__.py
    ├── config.py                       # Config file reader
    ├── preprocessing.py                # Grayscale, denoising, fast Otsu binarization
    ├── ocr_engine.py                   # Tesseract + Vision OCR wrapper
    ├── workers.py                      # Loader & processor implementations
    └── manager.py                      # Concurrency coordinator
```

---

## 3. Configuration (`config.txt`)

```ini
image_dir=dataset
n_workers=2
output_file=ocr_results.csv
```

---

## 4. Concurrency & Synchronization Design

- **Task Queue**: `multiprocessing.Queue(maxsize=300)` for dynamic load balancing.
- **Mutex Lock**: `multiprocessing.Lock()` protects the shared CSV file and atomic sequential ID counter (`multiprocessing.Value('i', 1)`).
- **Clean Termination**: Loader sends $n$ `None` sentinel tokens when done. Workers exit upon reading `None` (no deadlocks, no busy-waiting).
- **Process Model**: Uses `multiprocessing.Process` to bypass Python's GIL for true multi-core speedup.

---

## 5. Benchmarking & Speedup ($S = T_1 / T_n$)

Tested on the 100-image dataset:

| Workers ($n$) | Time ($T_n$) | Speedup ($S$) | Efficiency | Throughput |
| :---: | :---: | :---: | :---: | :---: |
| **1 worker** | 4.24 s | **1.00x** | 100.0% | 23.61 img/s |
| **2 workers** | 2.75 s | **1.54x** | 77.0% | 36.42 img/s |
| **4 workers** | **2.30 s** | **1.84x** (Optimal) | **46.0%** | **43.56 img/s** |
| **8 workers** | 2.74 s | 1.55x | 19.4% | 36.54 img/s |
| **12 workers** | 3.46 s | 1.22x | 10.2% | 28.89 img/s |

**Optimal Configuration**: $n = 4$ workers gives peak throughput (43.56 img/s) and lowest latency (2.30 s). Beyond 4 workers, IPC and lock overhead cause diminishing returns on 100 images.

---

## 6. How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run pipeline
python main.py

# 3. Run benchmarks
python benchmark.py

# 4. Generate presentation slides
python generate_presentation.py
```
