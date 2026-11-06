# OCR engine interface
# Uses Google Tesseract OCR (pytesseract) with our local eng.traineddata model

import os
import sys
import tempfile
from PIL import Image
import pytesseract

# Auto-detect Tesseract on Windows if it's installed in Program Files
if sys.platform == "win32":
    windows_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    for p in windows_paths:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            break

# Temp directory fallback for spawned worker processes
if "MPLCONFIGDIR" not in os.environ:
    os.environ["MPLCONFIGDIR"] = tempfile.gettempdir()

# Point Tesseract to eng.traineddata in the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TESSDATA_FILE = os.path.join(PROJECT_ROOT, "eng.traineddata")

if os.path.exists(TESSDATA_FILE):
    os.environ["TESSDATA_PREFIX"] = PROJECT_ROOT


# Extracts clean text string from a preprocessed in-memory image
def extract_text(image: Image.Image) -> str:
    config = f'--tessdata-dir "{PROJECT_ROOT}" -l eng' if os.path.exists(TESSDATA_FILE) else "-l eng"
    text = pytesseract.image_to_string(image, config=config)
    return " ".join(text.split())
