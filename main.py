"""
CSC611M Machine Project 1: Parallel OCR Pipeline
Main entry point. Loads config.txt and runs parallel OCR pipeline.
"""

import sys
import os
from pipeline.config import load_config
from pipeline.manager import run_pipeline


def main():
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.txt"

    if not os.path.exists(config_file):
        print(f"Error: Config file '{config_file}' not found.")
        sys.exit(1)

    config = load_config(config_file)
    run_pipeline(config)


if __name__ == "__main__":
    main()
