from resume_parser.services.candidate_profile import candidate_to_embedding_text
from resume_parser.services.vector_store import internship_to_text


def test_candidate_profile_contains_semantic_sections():
    candidate = {
        "full_name": "Alex",
        "skills": ["Python", "SQL"],
        "education": [{"degree": "B.Tech CSE", "dates": "2023-2027"}],
        "projects": [{"name": "RAG System", "description": "Built an internship retrieval system", "technologies": ["Python", "FAISS"]}],
    }
    text = candidate_to_embedding_text(candidate)
    assert "Technical Skills" not in text
    assert "Skills: Python; SQL" in text
    assert "Education:" in text
    assert "Projects:" in text
    assert "RAG System" in text


def test_internship_text_preserves_matching_fields():
    internship = {
        "title": "AI/ML Intern",
        "company": "TechNova",
        "description": "Build ML applications",
        "required_skills": ["Python", "Machine Learning"],
        "location": "Hyderabad",
        "work_mode": "Hybrid",
    }
    text = internship_to_text(internship)
    assert "Internship Title: AI/ML Intern" in text
    assert "Required Skills: Python, Machine Learning" in text
    assert "Work Mode: Hybrid" in text
