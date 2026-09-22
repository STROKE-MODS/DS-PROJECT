from __future__ import annotations

from pathlib import Path

import fitz


def extract_pdf_text(pdf_path: str | Path) -> str:
    """Extract selectable text from every page of a PDF in document order."""
    document = fitz.open(str(pdf_path))
    try:
        return "\n".join(page.get_text("text") for page in document).strip()
    finally:
        document.close()


def extract_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract text directly from uploaded PDF bytes before saving any profile data."""
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        return "\n".join(page.get_text("text") for page in document).strip()
    finally:
        document.close()


__all__ = ["extract_pdf_bytes", "extract_pdf_text"]
