"""
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
    """Plots clean, minimalist Execution Time, Speedup, and Efficiency charts."""
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 4.6))
    fig.patch.set_facecolor("#FFFFFF")

    w = df["workers"]
    c_primary = "#0E4D2B"
    c_blue = "#2563EB"
    c_accent = "#10B981"
    c_gray = "#94A3B8"

    # 1. Execution Time
    ax1.plot(w, df["exec_time_sec"], marker="o", color=c_blue, lw=2.2, markersize=7)
    ax1.set_title("Execution Time (s)", fontsize=12, fontweight="bold", pad=10)
    ax1.set_xlabel("Workers (n)", fontsize=10)
    ax1.set_ylabel("Seconds", fontsize=10)
    ax1.set_xticks(w)
    ax1.grid(True, linestyle="--", alpha=0.4)
    for x, y in zip(w, df["exec_time_sec"]):
        ax1.annotate(f"{y:.2f}s", (x, y), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8.5)

    # 2. Speedup
    ax2.plot(w, df["speedup"], marker="s", color=c_accent, lw=2.2, markersize=7, label="Observed (S = T1 / Tn)")
    ax2.plot(w, w, linestyle="--", color=c_gray, lw=1.5, label="Ideal Linear")
    ax2.set_title("Speedup vs Workers", fontsize=12, fontweight="bold", pad=10)
    ax2.set_xlabel("Workers (n)", fontsize=10)
    ax2.set_ylabel("Speedup Multiplier", fontsize=10)
    ax2.set_xticks(w)
    ax2.legend(fontsize=9, frameon=True)
    ax2.grid(True, linestyle="--", alpha=0.4)
    for x, y in zip(w, df["speedup"]):
        ax2.annotate(f"{y:.2f}x", (x, y), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8.5, fontweight="bold" if x == 4 else "normal")

    # 3. Efficiency
    ax3.plot(w, df["efficiency_pct"], marker="^", color=c_primary, lw=2.2, markersize=7)
    ax3.set_title("Parallel Efficiency (%)", fontsize=12, fontweight="bold", pad=10)
    ax3.set_xlabel("Workers (n)", fontsize=10)
    ax3.set_ylabel("Efficiency (%)", fontsize=10)
    ax3.set_xticks(w)
    ax3.set_ylim(0, 115)
    ax3.grid(True, linestyle="--", alpha=0.4)
    for x, y in zip(w, df["efficiency_pct"]):
        ax3.annotate(f"{y:.1f}%", (x, y), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"Plot saved to '{output_path}'.")


if __name__ == "__main__":
    run_benchmark()
