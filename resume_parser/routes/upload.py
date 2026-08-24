import json
import logging
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile

from resume_parser.config import OUTPUT_DIR, UPLOAD_DIR
from resume_parser.models.schema import ResumeParseResponse
from resume_parser.services.file_parser import extract_text_from_file
from resume_parser.services.llm_parser import extract_with_gemini
from resume_parser.services.merge import merge_extracted_data
from resume_parser.services.regex_parser import extract_regex_fields

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "application/octet-stream",  # Fallback for some browsers
}


@router.post("/parse-resume", response_model=ResumeParseResponse)
async def parse_resume(file: UploadFile = File(...)) -> ResumeParseResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected.")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file format. Please upload a PDF or DOCX file."
        )

    # Ensure output directories exist
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    file_id = str(uuid.uuid4())
    temp_path = UPLOAD_DIR / f"{file_id}_{Path(file.filename).name}"

    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if not temp_path.exists() or temp_path.stat().st_size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        text = extract_text_from_file(temp_path)
        if not text or not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract readable text from the uploaded file. Ensure it is not an image-only/scanned document."
            )

        regex_result = extract_regex_fields(text)

        try:
            llm_result = extract_with_gemini(text)
        except Exception as exc:
            logger.warning("Gemini extraction failed, falling back to regex: %s", exc)
            llm_result = {}

        merged = merge_extracted_data(regex_result, llm_result)

        output_path = OUTPUT_DIR / f"{file_id}.json"
        output_path.write_text(json.dumps(merged, indent=2), encoding="utf-8")

        return ResumeParseResponse(**merged)

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Resume parsing failed unexpectedly: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while parsing resume: {exc}"
        ) from exc
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass