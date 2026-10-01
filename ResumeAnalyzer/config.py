from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


BASE_DIR = _base_dir()
ASSETS_DIR = BASE_DIR / "assets"
REPORTS_DIR = BASE_DIR / "reports"
TEMP_DIR = BASE_DIR / "temp"
DATABASE_PATH = BASE_DIR / "resume_analyzer.db"
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
MAX_PDF_MB = int(os.getenv("MAX_PDF_MB", "5"))
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")
OCR_ENABLED = os.getenv("OCR_ENABLED", "true").strip().lower() not in {"0", "false", "no"}


def ensure_app_directories() -> None:
    ASSETS_DIR.mkdir(exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)
