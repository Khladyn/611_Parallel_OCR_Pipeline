# CSC611M Machine Project 1: Parallel OCR Pipeline
**Software Technology Department — De La Salle University**

---

## 1. Overview

Parallel OCR pipeline using Python standard library concurrency (`multiprocessing` / `threading`).
- **Loader Worker**: Scans `dataset/` and pushes images into a shared queue.
- **Processing Workers**: Pull images, preprocess, extract text, and append results to `ocr_results.csv`.
- **Synchronization**: Mutual exclusion lock protects CSV writing and atomic sequential IDs.
- **Model**: Integrates `eng.traineddata` for Google Tesseract OCR (`pytesseract`).

---

## 2. Project Structure

```
611_Parallel_OCR_Pipeline/
├── config.txt                          # Configuration (image_dir & n_workers)
├── main.py                             # Main entry point (supports --mode process/thread)
├── eng.traineddata                     # Tesseract English trained model
├── dataset/                            # 100 test images (img0001.png - img0100.png) + labels.txt
├── requirements.txt                    # Project dependencies
├── ocr_results.csv                     # Output results
├── benchmark.py                        # Unified benchmark runner
├── benchmark_results/                  # Generated benchmark charts and CSV metrics
├── preprocessing_demo/                 # 4-stage image demonstration assets
└── pipeline/
    ├── __init__.py
    ├── config.py                       # Config file reader
    ├── preprocessing.py                # Grayscale, denoising, contrast, fast Otsu
    ├── ocr_engine.py                   # Tesseract OCR wrapper (pytesseract)
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

## 6. How to Run (Cross-Platform)

This codebase is 100% cross-platform and runs natively on **Windows, macOS, and Linux**.

### Step 1: Install Tesseract Engine
* **Windows:** Download and run the [UB-Mannheim Tesseract Installer](https://github.com/UB-Mannheim/tesseract/wiki) (installs to `C:\Program Files\Tesseract-OCR\`).
* **macOS:** `brew install tesseract`
* **Linux (Ubuntu/Debian):** `sudo apt install tesseract-ocr`

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Pipeline

Run with default `config.txt` settings:
```bash
python main.py
```

Or switch between **Processes** and **Threads** directly via CLI arguments:
```bash
# Run with true multiprocessing (Process-based, GIL bypassed)
python main.py --mode process --workers 4

# Run with threading (Thread-based, shares interpreter memory)
python main.py --mode thread --workers 4
```

### Step 4: Run Reproducible Benchmarks

Run all benchmarks (saves charts and CSV metrics into `benchmark_results/`):
```bash
python benchmark.py --target all
```

Or target specific benchmarks individually:
```bash
# 1. Multi-worker Speedup & Amdahl's Law (1 to 12 workers -> benchmark_results/benchmark_speedup.png)
python benchmark.py --target speedup

# 2. Scaling & GIL analysis (100 vs. 500 images -> benchmark_results/scaling_comparison.png)
python benchmark.py --target scaling

# 3. Ground Truth Accuracy (Raw vs. Preprocessed -> benchmark_results/accuracy_benchmark.png)
python benchmark.py --target accuracy

# 4. Preprocessing 4-stage filter demo (benchmark_results/preprocessing_stages_*.png)
python benchmark.py --target preprocessing
```
