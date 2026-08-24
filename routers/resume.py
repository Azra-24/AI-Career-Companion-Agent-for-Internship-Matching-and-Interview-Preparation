import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database.connection import SessionLocal
from database.models import ParsedResume, Resume
from resume_parser.config import OUTPUT_DIR, UPLOAD_DIR
from resume_parser.services.file_parser import extract_text_from_file
from resume_parser.services.llm_parser import extract_with_gemini
from resume_parser.services.merge import merge_extracted_data
from resume_parser.services.regex_parser import extract_regex_fields
from routers.users import get_current_user
from schemas.resume_schema import ResumeUploadResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/resume", tags=["resume"])
upload_alias_router = APIRouter(prefix="/upload", tags=["resume"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "application/octet-stream",
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file selected.")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file format. Please upload a PDF or DOCX file."
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    file_id = str(uuid.uuid4())
    temp_path = UPLOAD_DIR / f"{file_id}_{Path(file.filename).name}"

    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if not temp_path.exists() or temp_path.stat().st_size == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

        text = extract_text_from_file(temp_path)
        regex_result = extract_regex_fields(text)

        try:
            llm_result = extract_with_gemini(text)
        except Exception as exc:
            logger.warning("Gemini extraction failed in resume router: %s", exc)
            llm_result = {}

        merged = merge_extracted_data(regex_result, llm_result)

        resume_record = Resume(
            user_id=current_user.user_id,
            file_name=file.filename,
            file_path=str(temp_path),
        )
        db.add(resume_record)
        db.commit()
        db.refresh(resume_record)

        parsed_resume = ParsedResume(
            resume_id=resume_record.resume_id,
            full_name=merged.get("full_name", ""),
            email=merged.get("email", ""),
            phone=merged.get("phone", ""),
            address=merged.get("address", ""),
            linkedin=merged.get("linkedin", ""),
            github=merged.get("github", ""),
            professional_summary=merged.get("professional_summary", ""),
            skills=merged.get("skills", []),
            technical_skills=merged.get("technical_skills", []),
            soft_skills=merged.get("soft_skills", []),
            education=merged.get("education", []),
            experience=merged.get("experience", []),
            projects=merged.get("projects", []),
            certifications=merged.get("certifications", []),
            internships=merged.get("internships", []),
            languages=merged.get("languages", []),
            achievements=merged.get("achievements", []),
            publications=merged.get("publications", []),
        )
        db.add(parsed_resume)
        db.commit()

        return ResumeUploadResponse(
            resume_id=resume_record.resume_id,
            parsed_resume=merged,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Resume upload failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while uploading resume."
        ) from exc
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass


@upload_alias_router.post("", response_model=ResumeUploadResponse)
async def upload_resume_alias(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeUploadResponse:
    return await upload_resume(file=file, current_user=current_user, db=db)