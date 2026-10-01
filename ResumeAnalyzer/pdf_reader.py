from __future__ import annotations

import os
import shutil
from pathlib import Path

import fitz
from docx import Document

from config import MAX_PDF_MB, OCR_ENABLED, TESSERACT_CMD


class PdfReadError(Exception):
    """Raised when a resume file cannot be read safely."""


SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def extract_text_from_file(file_path: str | Path) -> str:
    path = Path(file_path)
    _validate_resume_file(path)

    if path.suffix.lower() == ".pdf":
        return extract_text_from_pdf(path)
    if path.suffix.lower() == ".docx":
        return extract_text_from_docx(path)

    raise PdfReadError("Please select a PDF or DOCX resume.")


def _validate_resume_file(path: Path) -> None:
    if not path.exists():
        raise PdfReadError("Selected resume file does not exist.")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise PdfReadError("Please select a PDF or DOCX resume.")
    if path.stat().st_size > MAX_PDF_MB * 1024 * 1024:
        raise PdfReadError(f"Resume file is too large. Maximum size is {MAX_PDF_MB} MB.")


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    path = Path(pdf_path)
    _validate_resume_file(path)
    if path.suffix.lower() != ".pdf":
        raise PdfReadError("Please select a PDF resume.")

    try:
        document = fitz.open(path)
    except Exception as exc:
        raise PdfReadError("Could not open the PDF. It may be corrupted or password protected.") from exc

    pages: list[str] = []
    try:
        for page in document:
            pages.append(page.get_text("text"))
    finally:
        document.close()

    text = "\n".join(pages).strip()
    if len(text) >= 50:
        return text

    if not OCR_ENABLED:
        raise PdfReadError(
            "Could not extract enough text. OCR is disabled. Enable OCR_ENABLED=true or use a text-based PDF."
        )

    ocr_text = _extract_text_with_ocr(path)
    if len(ocr_text) < 50:
        raise PdfReadError(
            "Could not extract enough text from this PDF, even with OCR. Make sure the scan is clear."
        )
    return ocr_text


def _extract_text_with_ocr(pdf_path: Path) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise PdfReadError(
            "This PDF appears to be scanned. OCR support is missing. Install pytesseract and Pillow."
        ) from exc

    tesseract_executable = _find_tesseract_executable()
    if tesseract_executable:
        pytesseract.pytesseract.tesseract_cmd = tesseract_executable

    pages: list[str] = []
    try:
        document = fitz.open(pdf_path)
    except Exception as exc:
        raise PdfReadError("Could not open the PDF for OCR.") from exc

    try:
        for page in document:
            # 200 DPI is a reasonable quality/performance balance for resume scans.
            pixmap = page.get_pixmap(matrix=fitz.Matrix(200 / 72, 200 / 72), alpha=False)
            image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            pages.append(pytesseract.image_to_string(image))
    except Exception as exc:
        error_text = str(exc).lower()
        if "tesseract is not installed" in error_text or "tesseractnotfound" in error_text:
            raise PdfReadError(
                "OCR needs Tesseract OCR installed. Install Tesseract and optionally set TESSERACT_CMD in .env."
            ) from exc
        raise PdfReadError("OCR could not process this PDF. Try a clearer scan.") from exc
    finally:
        document.close()

    return "\n".join(pages).strip()


def extract_text_from_docx(docx_path: str | Path) -> str:
    path = Path(docx_path)
    _validate_resume_file(path)
    if path.suffix.lower() != ".docx":
        raise PdfReadError("Please select a DOCX resume.")

    try:
        document = Document(path)
    except Exception as exc:
        raise PdfReadError("Could not open the DOCX file. It may be corrupted or unsupported.") from exc

    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]

    table_text: list[str] = []
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                table_text.append(" | ".join(cells))

    text = "\n".join(paragraphs + table_text).strip()
    if len(text) < 50:
        raise PdfReadError("Could not extract enough text from the DOCX resume.")
    return text


def _find_tesseract_executable() -> str | None:
    """Find a Tesseract executable from explicit config, PATH, or common Windows paths."""
    if TESSERACT_CMD and Path(TESSERACT_CMD).exists():
        return TESSERACT_CMD

    on_path = shutil.which("tesseract")
    if on_path:
        return on_path

    if os.name == "nt":
        candidates = [
            Path(os.environ.get("ProgramFiles", "")) / "Tesseract-OCR" / "tesseract.exe",
            Path(os.environ.get("ProgramFiles(x86)", "")) / "Tesseract-OCR" / "tesseract.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Tesseract-OCR" / "tesseract.exe",
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
    return None
