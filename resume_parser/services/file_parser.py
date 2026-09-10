import logging
from pathlib import Path
from typing import Optional

import fitz
from docx import Document

logger = logging.getLogger(__name__)


def extract_text_from_file(file_path: Path) -> str:
    if not file_path.exists() or file_path.stat().st_size == 0:
        raise ValueError("Uploaded file is empty.")

    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    if suffix == ".docx":
        return extract_text_from_docx(file_path)
    if suffix in [".txt", ".text"]:
        return file_path.read_text(encoding="utf-8", errors="ignore").strip()
    raise ValueError("Unsupported file format. Please upload a PDF, DOCX, or TXT file.")


def extract_text_from_pdf(file_path: Path) -> str:
    try:
        doc = fitz.open(file_path)
        text_chunks = [page.get_text("text") for page in doc]
        doc.close()
        return "\n".join(chunk.strip() for chunk in text_chunks if chunk and chunk.strip())
    except Exception as exc:
        logger.exception("PDF parsing failed")
        raise ValueError("Failed to parse PDF file.") from exc


def extract_text_from_docx(file_path: Path) -> str:
    try:
        doc = Document(file_path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
        return "\n".join(paragraphs)
    except Exception as exc:
        logger.exception("DOCX parsing failed")
        raise ValueError("Failed to parse DOCX file.") from exc
