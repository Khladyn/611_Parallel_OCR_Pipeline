"""
OCR engine interface.
Supports Tesseract (pytesseract using eng.traineddata) with fallback to native Vision OCR.
"""

import os
import sys
import tempfile
from typing import Optional
from PIL import Image

# Temporary directory for matplotlib/spawned processes
if "MPLCONFIGDIR" not in os.environ:
    os.environ["MPLCONFIGDIR"] = tempfile.gettempdir()

# Locate eng.traineddata in project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TESSDATA_FILE = os.path.join(PROJECT_ROOT, "eng.traineddata")

if os.path.exists(TESSDATA_FILE):
    os.environ["TESSDATA_PREFIX"] = PROJECT_ROOT

_ENGINE: Optional[str] = None


def detect_engine() -> str:
    """Detect available OCR backend."""
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE

    # Try pytesseract with eng.traineddata
    try:
        import pytesseract
        _ = pytesseract.get_tesseract_version()
        _ENGINE = "pytesseract"
        return _ENGINE
    except Exception:
        pass

    # Fallback to macOS Apple Vision OCR
    if sys.platform == "darwin":
        try:
            import ocrmac
            _ENGINE = "ocrmac"
            return _ENGINE
        except Exception:
            pass

    raise RuntimeError("No OCR engine found. Install tesseract or ocrmac.")


def extract_text(image: Image.Image) -> str:
    """Extract text from preprocessed image."""
    engine = detect_engine()

    if engine == "pytesseract":
        import pytesseract
        config = f'--tessdata-dir "{PROJECT_ROOT}" -l eng' if os.path.exists(TESSDATA_FILE) else "-l eng"
        text = pytesseract.image_to_string(image, config=config)
        return " ".join(text.split())

    if engine == "ocrmac":
        from ocrmac.ocrmac import OCR
        annotations = OCR(image).recognize()
        lines = [item[0].strip() for item in annotations if item[0].strip()]
        return " ".join(lines)

    return ""
