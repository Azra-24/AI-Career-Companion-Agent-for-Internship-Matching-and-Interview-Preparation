import re
from typing import Any, Dict, List

# Common non-name headings to reject if matched by name regex
NAME_IGNORE_LIST = {
    "curriculum vitae",
    "resume",
    "contact information",
    "personal details",
    "career objective",
    "professional summary",
    "education",
    "experience",
    "work experience",
    "skills",
    "technical skills",
    "computer science",
    "software engineer",
    "bachelor of",
    "master of",
}

# Standard tech skills dictionary for regex fallback extraction
COMMON_SKILLS = [
    "python", "java", "c++", "c#", "c", "javascript", "typescript", "html", "css",
    "react", "angular", "vue", "node.js", "express", "django", "flask", "fastapi",
    "spring", "spring boot", "sql", "postgresql", "mysql", "sqlite", "mongodb",
    "redis", "docker", "kubernetes", "aws", "azure", "gcp", "git", "github",
    "linux", "machine learning", "deep learning", "nlp", "pandas", "numpy",
    "scikit-learn", "tensorflow", "pytorch", "rest api", "graphql", "faiss"
]


def extract_regex_fields(text: str) -> Dict[str, Any]:
    cleaned_text = text or ""
    name = extract_name(cleaned_text)
    email = extract_email(cleaned_text)
    phone = extract_phone(cleaned_text)
    linkedin = extract_url(cleaned_text, "linkedin")
    github = extract_url(cleaned_text, "github")
    skills = extract_skills(cleaned_text)

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "github": github,
        "skills": skills,
        "confidence": {
            "name": 0.7 if name else 0.0,
            "email": 0.95 if email else 0.0,
            "phone": 0.9 if phone else 0.0,
            "linkedin": 0.95 if linkedin else 0.0,
            "github": 0.95 if github else 0.0,
            "skills": 0.8 if skills else 0.0,
        },
    }


def extract_name(text: str) -> str:
    """
    Extract candidate name from the top lines of the resume text.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    # Check the first 5 non-empty lines where candidate names normally appear
    for line in lines[:5]:
        line_clean = line.lower().strip()
        if line_clean in NAME_IGNORE_LIST or any(kw in line_clean for kw in ["resume", "curriculum", "page"]):
            continue

        # Regex for 2-4 capitalized words (First [Middle] Last)
        match = re.match(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})$", line)
        if match:
            candidate = match.group(1).strip()
            if candidate.lower() not in NAME_IGNORE_LIST:
                return candidate

    return ""


def extract_email(text: str) -> str:
    match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
    return match.group(0).strip() if match else ""


def extract_phone(text: str) -> str:
    patterns = [
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        r"(?:\+?\d{1,3}[-.\s]?)?\d{10}\b",
        r"(?:\+?\d[\d\s\-\(\)]{8,15}\d)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            candidate = match.group(0).strip()
            # Verify candidate contains at least 10 digits
            digits_only = re.sub(r"\D", "", candidate)
            if 10 <= len(digits_only) <= 15:
                return candidate
    return ""


def extract_url(text: str, platform: str) -> str:
    patterns = {
        "linkedin": r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+/?",
        "github": r"(?:https?://)?(?:www\.)?github\.com/[\w\.\-]+/?",
    }
    match = re.search(patterns[platform], text, re.IGNORECASE)
    if match:
        url = match.group(0).strip()
        if not url.startswith("http"):
            url = f"https://{url}"
        return url
    return ""


def extract_skills(text: str) -> List[str]:
    """
    Regex fallback to catch common industry skills directly from text.
    """
    found_skills = set()
    text_lower = text.lower()

    for skill in COMMON_SKILLS:
        # Match whole words/symbols only
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found_skills.add(skill.title())

    return sorted(list(found_skills))