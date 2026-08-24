from typing import Any, Dict, Iterable


def _clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return "; ".join(part for item in value if (part := _clean(item)))
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            cleaned = _clean(item)
            if cleaned:
                parts.append(f"{key}: {cleaned}")
        return "; ".join(parts)
    return str(value)


def _section(title: str, value: Any) -> str:
    text = _clean(value)
    return f"{title}: {text}" if text else ""


def candidate_to_embedding_text(candidate: Dict[str, Any]) -> str:
    """Turn structured resume data into a semantically rich, deterministic document."""
    sections = [
        _section("Candidate", candidate.get("full_name")),
        _section("Professional Summary", candidate.get("professional_summary")),
        _section("Skills", candidate.get("skills")),
        _section("Technical Skills", candidate.get("technical_skills")),
        _section("Soft Skills", candidate.get("soft_skills")),
        _section("Education", candidate.get("education")),
        _section("Work Experience", candidate.get("experience") or candidate.get("work_experience")),
        _section("Internships", candidate.get("internships")),
        _section("Projects", candidate.get("projects")),
        _section("Certifications", candidate.get("certifications")),
        _section("Achievements", candidate.get("achievements")),
        _section("Languages", candidate.get("languages")),
        _section("Publications", candidate.get("publications")),
        _section("Additional Information", candidate.get("additional_info")),
    ]
    return "\n".join(section for section in sections if section)
