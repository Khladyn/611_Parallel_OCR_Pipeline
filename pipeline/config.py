"""
Configuration parser for Parallel OCR Pipeline.
Reads key-value parameters from config.txt.
"""

import os
from typing import Dict, Any


def load_config(config_path: str = "config.txt") -> Dict[str, Any]:
    """Load configuration from text file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # Default settings
    config: Dict[str, Any] = {
        "image_dir": "dataset",
        "n_workers": 2,
        "output_file": "ocr_results.csv",
        "backend": "process"
    }

    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, val = line.split("=", 1)
                key, val = key.strip(), val.strip()

                if key == "image_dir":
                    config["image_dir"] = val
                elif key == "n_workers":
                    config["n_workers"] = max(1, int(val))
                elif key == "output_file":
                    config["output_file"] = val
                elif key == "backend":
                    config["backend"] = "thread" if "thread" in val.lower() else "process"

    return config
