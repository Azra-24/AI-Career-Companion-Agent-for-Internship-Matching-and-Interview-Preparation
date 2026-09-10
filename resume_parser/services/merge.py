from typing import Any, Dict, List


def _ensure_list(val: Any) -> List[Any]:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    return [val]


def merge_extracted_data(
    regex_result: Dict[str, Any],
    llm_result: Dict[str, Any]
) -> Dict[str, Any]:
    regex_result = regex_result or {}
    llm_result = llm_result or {}

    contact_details = llm_result.get("contact_details", {})
    if not isinstance(contact_details, dict):
        contact_details = {}

    merged: Dict[str, Any] = {}

    # ---------------------------------------------------------
    # NAME
    # ---------------------------------------------------------
    merged["full_name"] = str(
        regex_result.get("name")
        or regex_result.get("full_name")
        or llm_result.get("full_name")
        or llm_result.get("name")
        or ""
    ).strip()

    merged["name"] = merged["full_name"]

    # ---------------------------------------------------------
    # CONTACT DETAILS
    # ---------------------------------------------------------
    merged["email"] = str(
        regex_result.get("email")
        or contact_details.get("email")
        or llm_result.get("email")
        or ""
    ).strip()

    merged["phone"] = str(
        regex_result.get("phone")
        or contact_details.get("phone")
        or llm_result.get("phone")
        or ""
    ).strip()

    merged["linkedin"] = str(
        regex_result.get("linkedin")
        or llm_result.get("linkedin")
        or ""
    ).strip()

    merged["github"] = str(
        regex_result.get("github")
        or llm_result.get("github")
        or ""
    ).strip()

    # ---------------------------------------------------------
    # ADDRESS & SUMMARY
    # ---------------------------------------------------------
    merged["address"] = str(
        contact_details.get("address")
        or llm_result.get("address")
        or ""
    ).strip()

    merged["professional_summary"] = str(
        llm_result.get("professional_summary")
        or llm_result.get("summary")
        or ""
    ).strip()

    # ---------------------------------------------------------
    # SKILLS (Combined & Deduplicated)
    # ---------------------------------------------------------
    llm_skills = _ensure_list(llm_result.get("skills"))
    regex_skills = _ensure_list(regex_result.get("skills"))
    
    # Preserve order while deduplicating
    combined_skills = []
    seen = set()
    for s in llm_skills + regex_skills:
        if s and isinstance(s, str) and s.strip().lower() not in seen:
            seen.add(s.strip().lower())
            combined_skills.append(s.strip())

    merged["skills"] = combined_skills
    merged["technical_skills"] = _ensure_list(llm_result.get("technical_skills"))
    merged["soft_skills"] = _ensure_list(llm_result.get("soft_skills"))

    # ---------------------------------------------------------
    # WORK, EDUCATION, PROJECTS, & MORE
    # ---------------------------------------------------------
    merged["education"] = _ensure_list(llm_result.get("education"))
    merged["experience"] = _ensure_list(
        llm_result.get("work_experience") or llm_result.get("experience")
    )
    merged["work_experience"] = merged["experience"]
    merged["projects"] = _ensure_list(llm_result.get("projects"))
    merged["certifications"] = _ensure_list(llm_result.get("certifications"))
    merged["internships"] = _ensure_list(llm_result.get("internships"))
    merged["languages"] = _ensure_list(llm_result.get("languages"))
    merged["achievements"] = _ensure_list(llm_result.get("achievements"))
    merged["publications"] = _ensure_list(llm_result.get("publications"))

    # ---------------------------------------------------------
    # ADDITIONAL INFO
    # ---------------------------------------------------------
    add_info = llm_result.get("additional_info", {})
    merged["additional_info"] = add_info if isinstance(add_info, dict) else {}

    return merged