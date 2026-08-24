from pydantic import BaseModel, Field
from typing import Any, List, Optional


class ResumeParseResponse(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    address: str = ""
    professional_summary: str = ""
    education: List[dict[str, Any]] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    experience: List[dict[str, Any]] = Field(default_factory=list)
    projects: List[dict[str, Any]] = Field(default_factory=list)
    certifications: List[dict[str, Any]] = Field(default_factory=list)
    internships: List[dict[str, Any]] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    publications: List[dict[str, Any]] = Field(default_factory=list)
    additional_info: Optional[dict[str, Any]] = None


class FileUploadResponse(BaseModel):
    message: str
    filename: str
    file_id: str
