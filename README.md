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

## 5. Benchmarking & Empirical Results

All benchmarks are reproducible via `python benchmark.py --target all`. Results and charts are generated directly in `benchmark_results/`.

### 5.1 Multi-Worker Speedup & Efficiency (100 Images)

Tested on the 100-image dataset using multiprocessing (`backend="process"`):

| Workers ($n$) | Time ($T_n$) | Speedup ($S$) | Parallel Efficiency ($E$) | Throughput |
| :---: | :---: | :---: | :---: | :---: |
| **1 worker** | 9.11 s | **1.00x** | 100.0% | 10.97 img/s |
| **2 workers** | 4.90 s | **1.86x** | 93.0% | 20.41 img/s |
| **4 workers** | **2.88 s** | **3.17x** (★ Sweet Spot) | **79.25%** | **34.77 img/s** |
| **8 workers** | 2.53 s | **3.60x** | 45.0% | 39.46 img/s |
| **12 workers** | 2.19 s | **4.16x** (Min Latency) | 34.67% | 45.70 img/s |

* **Optimal Configuration Analysis:**
  * **$n = 4$ workers is the Engineering Sweet Spot:** Captures a **68% execution time drop** (from 9.11s down to 2.88s) while maintaining **79.25% parallel efficiency**.
  * **Diminishing Returns (Amdahl's Law):** Tripling the worker pool from 4 to 12 workers ($3\times$ hardware allocation) only reduces runtime by an extra 0.69 seconds, causing efficiency to drop to **34.67%** as serial queue coordination, process spawn overhead, and CSV lock acquisition dominate.

---

### 5.2 Concurrency Comparison: Processes vs. Threads (100 vs. 500 Images)

Comparing `multiprocessing` against `threading` across small and scaled workloads:

* **100 Images Execution Time:**
  * **4 Workers:** Multiprocessing = **4.05s** | Threading = **2.12s**
  * **8 Workers:** Multiprocessing = **2.04s** | Threading = **1.08s** (Threads ~1.9x faster)
* **Throughput Scaling (100 vs. 500 Images):**
  * **N=4 (100 Imgs):** Process = 24.7 img/s | Thread = 47.1 img/s
  * **N=8 (100 Imgs):** Process = 49.1 img/s | Thread = 92.5 img/s
  * **N=4 (500 Imgs):** Process = 41.3 img/s | Thread = 46.1 img/s
  * **N=8 (500 Imgs):** Process = 71.3 img/s | Thread = 100.2 img/s
* **Key Takeaway:** Threads have zero process spawn latency and share memory freely in RAM. Because `pytesseract` invokes the native C++ Tesseract binary via subprocess, Python releases the GIL during inference, allowing threads to scale concurrently across physical cores.

---

### 5.3 Accuracy Benchmark: Raw vs. 4-Stage Preprocessed

Evaluated on all 100 images against ground truth labels (`dataset/labels.txt`):

* **Exact Word Match:** **71.0%** (Raw) $\rightarrow$ **80.0%** (Preprocessed) — **+9.0% absolute boost** (12.7% relative gain).
* **Character Accuracy (1 - CER):** **89.9%** (Raw) $\rightarrow$ **92.8%** (Preprocessed) — cuts character error rate by 28.4%.
* **Course Rubric Compliance:** Exceeds the course requirement of $\ge 50\%$ character recognition by **+42.8%**.
* **Word Recovery:** Three words completely omitted by raw OCR due to scanner noise (`ham`, `fordo`, `equip`) were fully recovered after Otsu binarization.

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
