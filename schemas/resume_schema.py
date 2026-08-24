from pydantic import BaseModel
from typing import Any, List


class ParsedResumeResponse(BaseModel):
    full_name: str = ''
    email: str = ''
    phone: str = ''
    linkedin: str = ''
    github: str = ''
    address: str = ''
    professional_summary: str = ''
    skills: List[str] = []
    technical_skills: List[str] = []
    soft_skills: List[str] = []
    education: List[Any] = []
    experience: List[Any] = []
    projects: List[Any] = []
    certifications: List[Any] = []
    internships: List[Any] = []
    languages: List[str] = []
    achievements: List[str] = []
    publications: List[Any] = []


class ResumeUploadResponse(BaseModel):
    resume_id: int
    parsed_resume: ParsedResumeResponse






'''uvicorn main:app --reload --port 8000'''