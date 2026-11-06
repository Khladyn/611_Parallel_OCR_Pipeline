# Main entry point
# Reads config.txt and launches the pipeline with optional command-line overrides

import os
import sys
import argparse
from pipeline.config import load_config
from pipeline.manager import run_pipeline


# Parses command line flags
def parse_args():
    parser = argparse.ArgumentParser(
        description="CSC611M Parallel OCR Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "config",
        nargs="?",
        default="config.txt",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--mode", "--backend", "-m",
        choices=["process", "thread"],
        help="Override concurrency backend: 'process' (multiprocessing) or 'thread' (threading)"
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        help="Override number of processing workers (e.g. 1, 2, 4, 8)"
    )
    parser.add_argument(
        "--images", "--dir", "-i",
        type=str,
        help="Override dataset directory path"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Override output CSV file path"
    )
    return parser.parse_args()


# Main function: loads settings and executes the pipeline
def main():
    args = parse_args()

    # Load configuration from config.txt
    if os.path.exists(args.config):
        config = load_config(args.config)
    else:
        if args.config != "config.txt":
            print(f"Error: Config file '{args.config}' not found.")
            sys.exit(1)
        config = {
            "image_dir": "dataset",
            "n_workers": 2,
            "output_file": "ocr_results.csv",
            "backend": "process"
        }

    # Apply CLI argument overrides if the user specified any
    if args.mode:
        config["backend"] = args.mode
    if args.workers is not None:
        config["n_workers"] = max(1, args.workers)
    if args.images:
        config["image_dir"] = args.images
    if args.output:
        config["output_file"] = args.output

    run_pipeline(config)


if __name__ == "__main__":
    main()
