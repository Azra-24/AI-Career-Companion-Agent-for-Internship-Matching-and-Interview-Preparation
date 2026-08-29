from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from resume_parser.app import app

client = TestClient(app)


def test_chat_assistant_valid_policy_query():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "The Internship Assistant platform parser accepts PDF and DOCX formats."
    mock_client.models.generate_content.return_value = mock_response

    payload = {
        "message": "Which file formats are supported for resume upload?",
        "candidate": {},
        "internships_context": []
    }

    with patch("routers.internships._get_gemini_client", return_value=mock_client):
        response = client.post("/internships/chat-assistant", json=payload)
        
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "PDF" in data["reply"] or "DOCX" in data["reply"]


def test_chat_assistant_out_of_scope_guardrail():
    # If out of scope, it should return the exact refusal string
    payload = {
        "message": "Who is Cristiano Ronaldo?",
        "candidate": {},
        "internships_context": []
    }

    # Should refuse even if Gemini returns something else because of our pre/post-processing check
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Cristiano Ronaldo is a famous football player."
    mock_client.models.generate_content.return_value = mock_response

    with patch("routers.internships._get_gemini_client", return_value=mock_client):
        response = client.post("/internships/chat-assistant", json=payload)
        
    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "I'm sorry, but I can only help with questions about the Internship Assistant product. For other inquiries, please contact product support."
