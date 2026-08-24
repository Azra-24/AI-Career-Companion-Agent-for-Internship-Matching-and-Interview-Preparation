import json
import logging
import os
import re
from typing import Any, Dict

from google import genai
from google.genai import types

from resume_parser.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Updated to the required current flash model
MODEL_NAME = "gemini-3.6-flash"


def _get_gemini_client() -> genai.Client:
    api_key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    api_key = api_key.strip().strip("'").strip('"')
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    return genai.Client(api_key=api_key)


def _empty_resume() -> Dict[str, Any]:
    return {
        "full_name": "",
        "contact_details": {
            "email": "",
            "phone": "",
            "address": ""
        },
        "address": "",
        "professional_summary": "",
        "skills": [],
        "technical_skills": [],
        "soft_skills": [],
        "education": [],
        "work_experience": [],
        "projects": [],
        "certifications": [],
        "internships": [],
        "achievements": [],
        "languages": [],
        "publications": [],
        "additional_info": {},
    }


def _extract_json_object(content: str) -> Dict[str, Any]:
    cleaned = (content or "").strip()
    if not cleaned:
        raise ValueError("Gemini returned an empty response.")

    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    try:
        val = json.loads(cleaned)
        if isinstance(val, dict):
            return val
    except json.JSONDecodeError:
        pass

    match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if match:
        try:
            val = json.loads(match.group(1))
            if isinstance(val, dict):
                return val
        except json.JSONDecodeError:
            pass

    start = cleaned.find("{")
    if start >= 0:
        decoder = json.JSONDecoder()
        try:
            val, _ = decoder.raw_decode(cleaned[start:])
            if isinstance(val, dict):
                return val
        except json.JSONDecodeError:
            pass

    raise ValueError("Gemini response did not contain a valid JSON object.")


def _normalise_result(value: Dict[str, Any]) -> Dict[str, Any]:
    result = _empty_resume()
    for key, val in value.items():
        if key in result:
            result[key] = val

    if not isinstance(result["contact_details"], dict):
        result["contact_details"] = {}

    for key in ("email", "phone", "address"):
        if not isinstance(result["contact_details"].get(key), str):
            result["contact_details"][key] = str(result["contact_details"].get(key) or "")

    list_fields = [
        "skills", "technical_skills", "soft_skills", "education",
        "work_experience", "projects", "certifications", "internships",
        "achievements", "languages", "publications"
    ]
    for field in list_fields:
        val = result.get(field)
        if val is None:
            result[field] = []
        elif not isinstance(val, list):
            result[field] = [val]

    for field in ("full_name", "address", "professional_summary"):
        val = result.get(field)
        result[field] = "" if val is None else str(val)

    if not isinstance(result.get("additional_info"), dict):
        result["additional_info"] = {}

    return result


def _build_prompt(text: str) -> str:
    schema = json.dumps(_empty_resume(), indent=2)
    return f"""
You are an expert resume information extraction system.
Extract information ONLY from the supplied resume text.

STRICT RULES:
1. NEVER invent information.
2. If a field is missing, return an empty string, empty list, or empty object.
3. Extract the full name accurately from the header or top of the resume.
4. Keep projects separate from employment.
5. Place internship experience in the internships field.

Return ONE valid JSON object matching this exact schema:
{schema}

RESUME TEXT:
{text}
""".strip()


def extract_with_gemini(text: str) -> Dict[str, Any]:
    if not text or not text.strip():
        return _empty_resume()

    client = _get_gemini_client()
    prompt = _build_prompt(text)

    try:
        config = types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=config,
        )

        content = getattr(response, "text", "") or ""
        parsed = _extract_json_object(content)
        return _normalise_result(parsed)

    except Exception as exc:
        logger.exception("Gemini extraction failed: %s", exc)
        raise RuntimeError(f"Gemini resume extraction failed: {exc}") from exc