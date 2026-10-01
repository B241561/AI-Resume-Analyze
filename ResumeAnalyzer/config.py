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

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip() or "openai/gpt-oss-120b"
MAX_PDF_MB = int(os.getenv("MAX_PDF_MB", "5"))
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")
OCR_ENABLED = os.getenv("OCR_ENABLED", "true").strip().lower() not in {"0", "false", "no"}

KEYRING_SERVICE = "AI Resume Analyzer"
KEYRING_ACCOUNT = "groq_api_key"


def get_stored_groq_api_key() -> str:
    try:
        import keyring

        return (keyring.get_password(KEYRING_SERVICE, KEYRING_ACCOUNT) or "").strip()
    except Exception:
        return ""


def get_groq_api_key() -> str:
    return get_stored_groq_api_key() or os.getenv("GROQ_API_KEY", "").strip()


def get_groq_key_source() -> str | None:
    if get_stored_groq_api_key():
        return "secure storage"
    if os.getenv("GROQ_API_KEY", "").strip():
        return "GROQ_API_KEY"
    return None


def save_groq_api_key(api_key: str) -> None:
    cleaned = (api_key or "").strip()
    if not cleaned:
        # Never include the supplied value in the error message.
        raise ValueError("API key is empty.")

    import keyring

    keyring.set_password(KEYRING_SERVICE, KEYRING_ACCOUNT, cleaned)


def remove_stored_groq_api_key() -> None:
    import keyring
    from keyring.errors import PasswordDeleteError

    try:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_ACCOUNT)
    except PasswordDeleteError:
        # Key already absent: nothing to remove.
        pass


def ensure_app_directories() -> None:
    ASSETS_DIR.mkdir(exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)