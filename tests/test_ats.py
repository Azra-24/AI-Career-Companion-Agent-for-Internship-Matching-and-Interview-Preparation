from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from resume_parser.app import app

client = TestClient(app)


def test_ats_score_success():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = """
    {
      "overall_score": 82,
      "grade": "Strong / Interview Ready",
      "breakdown": {
        "impact_metrics": 20,
        "action_verbs": 18,
        "section_completeness": 18,
        "technical_depth": 16,
        "formatting_clarity": 10
      },
      "strengths": ["Clear section layouts", "Good contact listing", "Quantified 1 database project"],
      "critical_improvements": ["Add numeric metrics to work experience", "Action verbs could be stronger"],
      "keyword_suggestions": ["FastAPI", "React", "Docker"]
    }
    """
    mock_client.models.generate_content.return_value = mock_response

    payload = {
        "candidate": {
            "full_name": "Shaik Azra Anisha",
            "email": "azrask24@gmail.com",
            "skills": ["Python", "Machine Learning", "SQL"],
            "education": [{"degree": "B.S. Computer Science"}],
            "projects": [{"name": "HashiraHelper", "description": "Built DB models"}],
            "experience": []
        }
    }

    with patch("routers.internships._get_gemini_client", return_value=mock_client):
        response = client.post("/internships/ats-score", json=payload)
        
    assert response.status_code == 200
    data = response.json()
    assert data["overall_score"] == 82
    assert data["grade"] == "Strong / Interview Ready"
    assert data["breakdown"]["impact_metrics"] == 20
    assert len(data["strengths"]) == 3
    assert "FastAPI" in data["keyword_suggestions"]
    mock_client.models.generate_content.assert_called_once()
