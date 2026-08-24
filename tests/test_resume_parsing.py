from services.regex_parser import extract_regex_fields
from services.merge import merge_extracted_data


def test_regex_extraction_extracts_common_fields():
    text = """
    John Doe
    john.doe@example.com
    +1-555-123-4567
    https://www.linkedin.com/in/johndoe
    https://github.com/johndoe
    """

    result = extract_regex_fields(text)

    assert result["name"] == "John Doe"
    assert result["email"] == "john.doe@example.com"
    assert result["phone"] == "+1-555-123-4567"
    assert result["linkedin"] == "https://www.linkedin.com/in/johndoe"
    assert result["github"] == "https://github.com/johndoe"


def test_merge_prefers_regex_for_priority_fields():
    regex_result = {
        "name": "Jane Doe",
        "email": "regex@example.com",
        "phone": "+1-222-333-4444",
        "linkedin": "https://linkedin.com/in/regex",
        "github": "https://github.com/regex",
        "professional_summary": "",
        "skills": [],
    }
    llm_result = {
        "name": "LLM Name",
        "email": "llm@example.com",
        "phone": "+1-999-999-9999",
        "linkedin": "https://linkedin.com/in/llm",
        "github": "https://github.com/llm",
        "professional_summary": "A skilled engineer.",
        "skills": ["Python"],
    }

    merged = merge_extracted_data(regex_result, llm_result)

    assert merged["email"] == "regex@example.com"
    assert merged["phone"] == "+1-222-333-4444"
    assert merged["linkedin"] == "https://linkedin.com/in/regex"
    assert merged["github"] == "https://github.com/regex"
    assert merged["name"] == "Jane Doe"
    assert merged["professional_summary"] == "A skilled engineer."
    assert merged["skills"] == ["Python"]


def test_llm_normalisation_handles_missing_sections_without_inventing_values():
    from resume_parser.services.llm_parser import _normalise_result

    result = _normalise_result({"full_name": "Alex", "skills": ["Python"]})

    assert result["full_name"] == "Alex"
    assert result["skills"] == ["Python"]
    assert result["education"] == []
    assert result["work_experience"] == []
    assert result["projects"] == []
    assert result["certifications"] == []


def test_llm_json_recovery_accepts_markdown_fence_and_extra_text():
    from resume_parser.services.llm_parser import _extract_json_object

    result = _extract_json_object('Here is the result:\n```json\n{"full_name":"Alex"}\n```')
    assert result == {"full_name": "Alex"}
