"""
Automated benchmarking script.
Tests pipeline across worker counts, calculates speedup S = T1 / Tn, and generates plots.
"""

import os
import tempfile
import pandas as pd
import matplotlib.pyplot as plt

os.environ["MPLCONFIGDIR"] = tempfile.gettempdir()

from pipeline.manager import run_pipeline


def run_benchmark(
    worker_counts=(1, 2, 4, 8, 12),
    image_dir="dataset",
    runs=2,
    plot_file="benchmark_speedup.png",
    csv_file="benchmark_results.csv"
):
    print("=" * 60)
    print("RUNNING BENCHMARKS")
    print(f"Workers: {worker_counts} | Runs per config: {runs}")
    print("=" * 60)

    # Initial warmup run
    run_pipeline({"image_dir": image_dir, "n_workers": 2, "output_file": "ocr_temp.csv"})

    records = []
    t1_base = None

    for n in worker_counts:
        print(f"\n--- Testing with {n} Worker(s) ---")
        times = []
        for r in range(runs):
            out_csv = f"ocr_w{n}_r{r}.csv"
            res = run_pipeline({"image_dir": image_dir, "n_workers": n, "output_file": out_csv})
            times.append(res["total_time_sec"])
            if os.path.exists(out_csv):
                os.remove(out_csv)

        avg_time = round(sum(times) / len(times), 4)
        if n == 1:
            t1_base = avg_time

        speedup = round(t1_base / avg_time, 2)
        efficiency = round((speedup / n) * 100, 2)
        throughput = round(res["total_images"] / avg_time, 2)

        records.append({
            "workers": n,
            "exec_time_sec": avg_time,
            "speedup": speedup,
            "efficiency_pct": efficiency,
            "throughput_ips": throughput
        })

    # Clean warmup file
    if os.path.exists("ocr_temp.csv"):
        os.remove("ocr_temp.csv")

    df = pd.DataFrame(records)
    df.to_csv(csv_file, index=False)

    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print(df.to_string(index=False))
    print("=" * 60)

    # Generate charts
    plot_results(df, plot_file)
    return df


def plot_results(df: pd.DataFrame, output_path: str):
    """Plots Execution Time, Speedup, and Efficiency."""
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16, 5))
    fig.patch.set_facecolor("#FAFAFA")

    w = df["workers"]

    # 1. Execution Time
    ax1.plot(w, df["exec_time_sec"], marker="o", color="#1F77B4", lw=2)
    ax1.set_title("Execution Time (s)")
    ax1.set_xlabel("Workers (n)")
    ax1.set_xticks(w)
    ax1.grid(True, linestyle="--", alpha=0.5)

    # 2. Speedup
    ax2.plot(w, df["speedup"], marker="s", color="#2CA02C", lw=2, label="Observed Speedup")
    ax2.plot(w, w, linestyle="--", color="#7F7F7F", lw=1.5, label="Ideal Linear")
    ax2.set_title("Speedup (S = T1 / Tn)")
    ax2.set_xlabel("Workers (n)")
    ax2.set_xticks(w)
    ax2.legend()
    ax2.grid(True, linestyle="--", alpha=0.5)

    # 3. Efficiency
    ax3.plot(w, df["efficiency_pct"], marker="^", color="#FF7F0E", lw=2)
    ax3.set_title("Parallel Efficiency (%)")
    ax3.set_xlabel("Workers (n)")
    ax3.set_xticks(w)
    ax3.set_ylim(0, 110)
    ax3.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Plot saved to '{output_path}'.")


if __name__ == "__main__":
    run_benchmark()
