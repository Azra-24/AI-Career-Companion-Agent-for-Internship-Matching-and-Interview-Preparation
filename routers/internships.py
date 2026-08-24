import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from resume_parser.config import UPLOAD_DIR, GEMINI_API_KEY
from resume_parser.services.candidate_profile import candidate_to_embedding_text
from resume_parser.services.file_parser import extract_text_from_file
from resume_parser.services.internship_matcher import (
    build_internship_index,
    explain_matches,
    load_internships,
    search_internships,
)
from resume_parser.services.llm_parser import extract_with_gemini
from resume_parser.services.merge import merge_extracted_data
from resume_parser.services.regex_parser import extract_regex_fields

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/internships", tags=["internships"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "application/octet-stream",
}


# =========================================================
# Request / Response Models
# =========================================================

class MatchRequest(BaseModel):
    candidate: Dict[str, Any]
    top_k: int = Field(default=5, ge=1, le=10)
    include_explanation: bool = True


class IndexResponse(BaseModel):
    indexed_internships: int


# =========================================================
# Internship Catalog
# =========================================================

@router.get("")
def internship_catalog() -> List[Dict[str, Any]]:
    return load_internships()


# =========================================================
# Build FAISS Internship Index
# =========================================================

@router.post("/index", response_model=IndexResponse)
def create_internship_index() -> IndexResponse:
    try:
        count = build_internship_index()
        return IndexResponse(indexed_internships=count)
    except Exception as exc:
        logger.exception("Failed to build index: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# =========================================================
# Match Existing Candidate JSON
# =========================================================

@router.post("/match", response_model=Dict[str, Any])
def match_candidate(request: MatchRequest) -> Dict[str, Any]:
    try:
        if not candidate_to_embedding_text(request.candidate):
            raise HTTPException(
                status_code=400,
                detail="Candidate data is empty or invalid."
            )

        matches = search_internships(request.candidate, request.top_k)
        explanation = explain_matches(request.candidate, matches) if request.include_explanation else ""

        return {
            "candidate": request.candidate,
            "matches": matches,
            "explanation": explanation,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Candidate matching failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# =========================================================
# Upload Resume → Parse → Embed → Match
# =========================================================

@router.post("/match-resume", response_model=Dict[str, Any])
async def match_uploaded_resume(file: UploadFile = File(...)) -> Dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected.")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file format. Please upload a PDF or DOCX resume."
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_id = str(uuid.uuid4())
    temp_path = UPLOAD_DIR / f"match_{file_id}_{Path(file.filename).name}"

    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if not temp_path.exists() or temp_path.stat().st_size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        text = extract_text_from_file(temp_path)
        if not text or not text.strip():
            raise HTTPException(
                status_code=422,
                detail="Could not extract text from the resume. Please ensure the file contains selectable text."
            )

        regex_result = extract_regex_fields(text)

        try:
            llm_result = extract_with_gemini(text)
        except Exception as exc:
            logger.warning("Gemini extraction failed, using regex fallback: %s", exc)
            llm_result = {}

        candidate = merge_extracted_data(regex_result, llm_result)
        candidate_text = candidate_to_embedding_text(candidate)

        if not candidate_text or not candidate_text.strip():
            raise HTTPException(
                status_code=422,
                detail="Not enough information could be extracted for internship matching."
            )

        matches = search_internships(candidate, top_k=5)
        explanation = explain_matches(candidate, matches)

        return {
            "candidate": candidate,
            "matches": matches,
            "explanation": explanation,
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Resume matching pipeline failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass


class CoverLetterRequest(BaseModel):
    candidate: Dict[str, Any]
    internship_title: str
    company: str
    tone: Optional[str] = "Formal & Professional"
    emphasis: Optional[str] = None


def _get_gemini_client() -> genai.Client:
    api_key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    api_key = api_key.strip().strip("'").strip('"')
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    return genai.Client(api_key=api_key)


def build_cover_letter_prompt(candidate: dict, internship_title: str, company: str, tone: str, emphasis: str) -> str:
    import datetime
    current_date = datetime.date.today().strftime("%B %d, %Y")
    
    full_name = candidate.get("full_name", "")
    email = candidate.get("email", "")
    phone = candidate.get("phone", "")
    skills = candidate.get("skills", [])
    technical_skills = candidate.get("technical_skills", [])
    soft_skills = candidate.get("soft_skills", [])
    education = candidate.get("education", [])
    projects = candidate.get("projects", [])
    experience = candidate.get("experience", []) or candidate.get("work_experience", []) or candidate.get("internships", [])
    
    all_skills = list(set(skills + technical_skills + soft_skills))
    skills_str = ", ".join(all_skills) if all_skills else "Not provided"
    
    def format_list_item(item):
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            return "; ".join(f"{k}: {v}" for k, v in item.items() if v)
        return str(item)

    projects_str = "\n".join(f"- {format_list_item(p)}" for p in projects) if projects else "Not provided"
    experience_str = "\n".join(f"- {format_list_item(e)}" for e in experience) if experience else "Not provided"
    education_str = "\n".join(f"- {format_list_item(ed)}" for ed in education) if education else "Not provided"

    prompt = f"""
You are an expert career advisor. Write a personalized, professional cover letter for the candidate applying to the target internship.

CANDIDATE INFORMATION:
- Name: {full_name}
- Email: {email}
- Phone: {phone}
- Skills: {skills_str}
- Education: {education_str}
- Projects: {projects_str}
- Professional Experience / Internships: {experience_str}

TARGET ROLE DETAILS:
- Internship Title: {internship_title}
- Company: {company}
- Current Date: {current_date}

CONSTRAINTS & STYLE:
- Tone: {tone or "Formal & Professional"}
- Custom Emphasis (Highlight these aspects): {emphasis or "None specified"}

STRICT GROUNDING RULES:
1. ONLY use the candidate's verified projects, technical skills, experience, and education from their profile.
2. STRICTLY DO NOT invent, hallucinate, or extrapolate credentials, projects, employment, metrics, or qualifications not explicitly provided.
3. Connect the candidate's existing skills/projects directly to the target role at {company}.

STRUCTURE:
Please structure the letter exactly as a formal business cover letter with the following elements and double line breaks between sections for clean readability:

[Candidate Name]
[Candidate Email]
[Candidate Phone]
[Current Date]

Hiring Team
[Company Name]

Dear Hiring Team at [Company Name],

[Paragraph 1: Introduction/Hook]
Introduce yourself, state the internship role you are applying for, and outline your educational background.

[Paragraph 2: Technical Alignment & Project Evidence]
Highlight your technical skills and reference actual projects from your candidate profile (such as HashiraHelper, ML models, or others present in the projects list) that match the target role and emphasis.

[Paragraph 3: Company Alignment & Value Proposition]
Demonstrate your excitement about working at [Company Name] specifically, aligning your goals with their mission.

[Paragraph 4: Strong Closing & Call-to-Action]
Conclude professionally, restating your interest, mentioning availability for an interview, and ending with a polite sign-off.

Sincerely,
[Candidate Name]

Begin drafting the letter directly. Use two clean line breaks (double line breaks) between each paragraph/block.
"""
    return prompt.strip()


@router.post("/generate-cover-letter", response_model=Dict[str, Any])
def generate_cover_letter(request: CoverLetterRequest) -> Dict[str, Any]:
    try:
        client = _get_gemini_client()
        prompt = build_cover_letter_prompt(
            candidate=request.candidate,
            internship_title=request.internship_title,
            company=request.company,
            tone=request.tone,
            emphasis=request.emphasis
        )
        
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
            )
        )
        
        cover_letter = getattr(response, "text", "") or ""
        if not cover_letter or not cover_letter.strip():
            raise HTTPException(status_code=500, detail="Gemini returned an empty cover letter.")
            
        return {"cover_letter": cover_letter}
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Cover letter generation failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate cover letter: {str(exc)}"
        )


import json
import datetime

APPLICATIONS_FILE = Path(__file__).parent.parent / "database" / "applications.json"
APPLICATIONS = []

# Load initial applications from JSON
try:
    if APPLICATIONS_FILE.exists():
        with open(APPLICATIONS_FILE, "r", encoding="utf-8") as f:
            APPLICATIONS = json.load(f)
except Exception as e:
    logger.error("Failed to load applications from file: %s", e)


class ApplyRequest(BaseModel):
    user_email: str
    internship_id: Optional[str] = None
    internship_title: str
    company: str
    required_skills: List[str] = []
    candidate_skills: List[str] = []


@router.post("/apply", response_model=Dict[str, Any])
def apply_to_internship(request: ApplyRequest) -> Dict[str, Any]:
    try:
        # Normalize skill comparison (case-insensitive)
        cand_skills_lower = {s.lower() for s in request.candidate_skills}
        matched = []
        missing = []
        
        for skill in request.required_skills:
            if skill.lower() in cand_skills_lower:
                matched.append(skill)
            else:
                missing.append(skill)
        
        total_req = len(request.required_skills)
        readiness_score = (len(matched) / max(total_req, 1)) * 100.0
        
        # Build learning recommendations for missing skills
        learning_recs = []
        for s in missing:
            learning_recs.append(f"Complete a tutorial/project focusing on {s} to close the gap.")
        if not learning_recs:
            learning_recs.append("All required skills met! Review core concepts and practice behaviour questions.")
            
        applied_date = datetime.date.today().strftime("%Y-%m-%d")
        
        stages = [
            {"stage": "Resume Submitted", "status": "Completed"},
            {"stage": "Skill & Profile Screening", "status": "In Progress"},
            {"stage": "Technical Assessment", "status": "Upcoming"},
            {"stage": "Manager Interview", "status": "Upcoming"},
            {"stage": "Final Offer", "status": "Pending"}
        ]
        
        app_id = f"APP-{len(APPLICATIONS) + 101}"
        app_obj = {
            "id": app_id,
            "user_email": request.user_email,
            "internship_title": request.internship_title,
            "company": request.company,
            "mode": "Hybrid • 6 months",
            "applied_date": applied_date,
            "status": "Screening",
            "readiness_score": readiness_score,
            "matched_skills": matched,
            "missing_skills": missing,
            "preferred_missing": [],
            "application_stages": stages,
            "learning_recommendations": learning_recs
        }
        
        APPLICATIONS.append(app_obj)
        
        # Save to applications.json
        try:
            APPLICATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(APPLICATIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(APPLICATIONS, f, indent=2)
        except Exception as e:
            logger.error("Failed to save application to file: %s", e)
            
        return app_obj
    except Exception as exc:
        logger.exception("Failed to submit application: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to submit application: {str(exc)}")


@router.get("/applications", response_model=List[Dict[str, Any]])
def get_applications(email: Optional[str] = None) -> List[Dict[str, Any]]:
    if email:
        return [app for app in APPLICATIONS if app["user_email"] == email]
    return APPLICATIONS


class ATSRequest(BaseModel):
    candidate: Dict[str, Any]
    raw_text: Optional[str] = None


def build_ats_scoring_prompt(candidate: dict, raw_text: str = "") -> str:
    import json
    candidate_str = json.dumps(candidate, indent=2)
    prompt = f"""
You are an expert Applicant Tracking System (ATS) auditor and career strategist.
Evaluate the candidate's resume profile and raw resume text (if provided) and score it across 5 specific categories:

1. impact_metrics (0-25 points): Check for the presence of numbers, percentages, dollar values, benchmarks, and quantifiable business/engineering achievements.
2. action_verbs (0-20 points): Evaluate the use of strong engineering and professional action verbs (e.g., "designed", "architected", "optimized", "spearheaded") rather than weak or passive voice (e.g., "helped", "responsible for").
3. section_completeness (0-20 points): Score the presence and thoroughness of key sections: name, contact info, education, projects, work experience/internships, and technical skills.
4. technical_depth (0-20 points): Look for the depth, breadth, and naming of technical tools, libraries, languages, and frameworks.
5. formatting_clarity (0-15 points): Assess the formatting layout logic, brevity, logical flow, and ease of parser readability.

CRITICAL RULES:
- Category scores MUST sum up to the overall_score.
- Keep recommendations and feedback strictly realistic and grounded in the candidate's field.
- Provide a Grade/Status:
  * "Strong / Interview Ready" if overall_score is >= 80.
  * "Needs Optimization" if overall_score is < 80.

CANDIDATE PROFILE:
{candidate_str}

RAW RESUME TEXT:
{raw_text or "Not provided"}

Return a single JSON object matching this exact schema:
{{
  "overall_score": int,
  "grade": str,
  "breakdown": {{
    "impact_metrics": int,
    "action_verbs": int,
    "section_completeness": int,
    "technical_depth": int,
    "formatting_clarity": int
  }},
  "strengths": [str, str, str, str],
  "critical_improvements": [str, str, str, str],
  "keyword_suggestions": [str, str, str, str, str]
}}
"""
    return prompt.strip()


@router.post("/ats-score", response_model=Dict[str, Any])
def get_ats_score(request: ATSRequest) -> Dict[str, Any]:
    try:
        client = _get_gemini_client()
        prompt = build_ats_scoring_prompt(request.candidate, request.raw_text or "")
        
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
            )
        )
        
        content = getattr(response, "text", "") or ""
        parsed = json.loads(content)
        
        breakdown = parsed.get("breakdown", {})
        impact = int(breakdown.get("impact_metrics", 0))
        verbs = int(breakdown.get("action_verbs", 0))
        completeness = int(breakdown.get("section_completeness", 0))
        depth = int(breakdown.get("technical_depth", 0))
        formatting = int(breakdown.get("formatting_clarity", 0))
        
        impact = max(0, min(25, impact))
        verbs = max(0, min(20, verbs))
        completeness = max(0, min(20, completeness))
        depth = max(0, min(20, depth))
        formatting = max(0, min(15, formatting))
        
        total_score = impact + verbs + completeness + depth + formatting
        grade = "Strong / Interview Ready" if total_score >= 80 else "Needs Optimization"
        
        return {
            "overall_score": total_score,
            "grade": grade,
            "breakdown": {
                "impact_metrics": impact,
                "action_verbs": verbs,
                "section_completeness": completeness,
                "technical_depth": depth,
                "formatting_clarity": formatting
            },
            "strengths": parsed.get("strengths", []),
            "critical_improvements": parsed.get("critical_improvements", []),
            "keyword_suggestions": parsed.get("keyword_suggestions", [])
        }
    except Exception as exc:
        logger.exception("ATS Resume Scorer failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"ATS scoring failed: {str(exc)}")


class ChatRequest(BaseModel):
    message: str
    candidate: Optional[Dict[str, Any]] = None
    internships_context: Optional[List[Dict[str, Any]]] = None


def build_chat_prompt(message: str, candidate: Optional[dict] = None, internships: Optional[list] = None) -> str:
    import json
    candidate_str = json.dumps(candidate, indent=2) if candidate else "None provided"
    internships_str = json.dumps(internships, indent=2) if internships else "None provided"
    
    prompt = f"""
You are an expert Technical Career Coach and AI Recruiter.
Help the candidate with their career query, keeping your answers concise, actionable, and formatted with clean bullet points.
Use the candidate's actual projects, skills, and matched internships as context.

CANDIDATE PROFILE:
{candidate_str}

MATCHED INTERNSHIPS CONTEXT:
{internships_str}

USER QUERY:
{message}

Answer the candidate directly. Do not use generic introductions or formatting headers like "Answer:". Focus on role-specific interview preparation, resume tailoring advice, and career roadmaps as requested.
"""
    return prompt.strip()


@router.post("/chat-assistant", response_model=Dict[str, Any])
def chat_assistant(request: ChatRequest) -> Dict[str, Any]:
    try:
        client = _get_gemini_client()
        prompt = build_chat_prompt(request.message, request.candidate, request.internships_context)
        
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
            )
        )
        
        reply = getattr(response, "text", "") or "I'm sorry, I could not generate a response. Please try again."
        return {"reply": reply}
    except Exception as exc:
        logger.exception("Chat assistant failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Chat assistant failed: {str(exc)}")