from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from resume_parser.app import app

client = TestClient(app)


def test_chat_assistant_success():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Hello! To improve your score, I recommend: * Quantifying your RAG models achievements * Adding Python keywords."
    mock_client.models.generate_content.return_value = mock_response

    payload = {
        "message": "How can I improve my match readiness for top roles?",
        "candidate": {
            "full_name": "Shaik Azra Anisha",
            "skills": ["Python", "SQL"]
        },
        "internships_context": []
    }

    with patch("routers.internships._get_gemini_client", return_value=mock_client):
        response = client.post("/internships/chat-assistant", json=payload)
        
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "improve your score" in data["reply"]
    mock_client.models.generate_content.assert_called_once()
