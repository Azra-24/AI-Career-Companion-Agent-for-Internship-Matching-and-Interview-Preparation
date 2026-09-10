from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from resume_parser.app import app

client = TestClient(app)


def test_generate_cover_letter_success():
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Dear Hiring Team,\n\nI am writing to express my enthusiasm for the AI/ML Intern position at TechCorp.\n\nDuring my project working on the RAG System, I applied Python and SQL to build reliable pipelines.\n\nTechCorp is an industry leader and I am excited about the prospect of contributing to your team.\n\nThank you for your time and consideration."
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    payload = {
        "candidate": {
            "full_name": "John Doe",
            "email": "john@example.com",
            "skills": ["Python", "SQL"],
            "education": [{"degree": "B.S. Computer Science"}],
            "projects": [{"name": "RAG System"}],
            "experience": [{"role": "Software Engineering Intern"}]
        },
        "internship_title": "AI/ML Intern",
        "company": "TechCorp",
        "tone": "Confident",
        "emphasis": "Highlight the RAG System project"
    }

    with patch("routers.internships._get_groq_client", return_value=mock_client):
        response = client.post("/internships/generate-cover-letter", json=payload)
        
    assert response.status_code == 200
    data = response.json()
    assert "cover_letter" in data
    assert "AI/ML Intern" in data["cover_letter"]
    assert "RAG System" in data["cover_letter"]
    mock_client.chat.completions.create.assert_called_once()


def test_generate_cover_letter_failure():
    with patch("routers.internships._get_groq_client", side_effect=Exception("API Key expired")):
        payload = {
            "candidate": {
                "full_name": "John Doe",
                "email": "john@example.com",
                "skills": ["Python"],
                "education": [],
                "projects": [],
                "experience": []
            },
            "internship_title": "AI/ML Intern",
            "company": "TechCorp"
        }
        response = client.post("/internships/generate-cover-letter", json=payload)
        
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "Failed to generate cover letter" in data["detail"]
