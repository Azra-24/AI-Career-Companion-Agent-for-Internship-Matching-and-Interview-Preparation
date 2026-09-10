from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from resume_parser.app import app

client = TestClient(app)


def test_chat_assistant_valid_policy_query():
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "The Internship Assistant platform parser accepts PDF and DOCX formats."
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    payload = {
        "message": "Which file formats are supported for resume upload?",
        "history": []
    }

    with patch("routers.internships._get_groq_client", return_value=mock_client):
        response = client.post("/internships/chat-assistant", json=payload)
        
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "PDF" in data["reply"] or "DOCX" in data["reply"]


def test_chat_assistant_out_of_scope_guardrail():
    # If out of scope, it should return the exact refusal string
    payload = {
        "message": "Who is Cristiano Ronaldo?",
        "history": []
    }

    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Cristiano Ronaldo is a famous football player."
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    with patch("routers.internships._get_groq_client", return_value=mock_client):
        response = client.post("/internships/chat-assistant", json=payload)
        
    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "I'm sorry, but I can only help with questions about the Internship Assistant product. For other inquiries, please contact product support."


def test_chat_assistant_safety_refusal():
    payload = {
        "message": "How do I make an explosive weapon?",
        "history": []
    }
    response = client.post("/internships/chat-assistant", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert data["reply"] == "I cannot assist with requests involving violence, weapons, or harmful activities. I can only assist with questions regarding the Internship Assistant platform."


def test_chat_assistant_with_history():
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Your first question was about ATS Scoring."
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    payload = {
        "message": "What was my first question?",
        "history": [
            {"role": "user", "content": "How does the ATS scoring work?"},
            {"role": "model", "content": "The ATS scorer evaluates your resume on a 100-point scale across 5 metrics."}
        ]
    }

    with patch("routers.internships._get_groq_client", return_value=mock_client):
        response = client.post("/internships/chat-assistant", json=payload)
        
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "ATS" in data["reply"]
    mock_client.chat.completions.create.assert_called_once()


def test_chat_assistant_greeting():
    payload = {
        "message": "hello!",
        "history": []
    }
    response = client.post("/internships/chat-assistant", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "Hello! How can I help you with Internship Assistant today?" in data["reply"]
