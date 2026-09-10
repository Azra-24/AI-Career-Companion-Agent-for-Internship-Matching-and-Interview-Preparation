import io
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from resume_parser.app import app

client = TestClient(app)


def test_upload_prep_doc_success():
    file_content = b"Candidate Study Notes: Review REST API design, Python GIL, and SQL Indexing."
    file = io.BytesIO(file_content)
    
    response = client.post(
        "/internships/upload-prep-doc",
        files={"file": ("study_notes.txt", file, "text/plain")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "study_notes.txt"
    assert "REST API design" in data["extracted_text"]


def test_upload_prep_doc_invalid_extension():
    file = io.BytesIO(b"executable binary")
    response = client.post(
        "/internships/upload-prep-doc",
        files={"file": ("malware.exe", file, "application/octet-stream")}
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_interview_prep_assistant_role_recommendation():
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Based on your resume, you are well suited for AI/ML Intern and Python Backend Engineer roles."
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    payload = {
        "message": "Which role can I apply for based on my resume?",
        "candidate_profile": {
            "full_name": "Shaik Azra Anisha",
            "skills": ["Python", "Machine Learning", "SQL", "FastAPI"],
            "education": [{"degree": "B.S. Computer Science"}]
        }
    }

    with patch("routers.internships._get_groq_client", return_value=mock_client):
        response = client.post("/internships/interview-prep-assistant", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "AI/ML Intern" in data["reply"]
    mock_client.chat.completions.create.assert_called_once()


def test_interview_prep_assistant_doc_qa():
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "The uploaded job description requires 1 year experience with Docker and Kubernetes."
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    payload = {
        "message": "What are the core requirements in the uploaded document?",
        "document_context": "Job Description: We require Docker, Kubernetes, and Golang experience.",
        "target_role": "DevOps Intern"
    }

    with patch("routers.internships._get_groq_client", return_value=mock_client):
        response = client.post("/internships/interview-prep-assistant", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "Docker" in data["reply"]
    mock_client.chat.completions.create.assert_called_once()


def test_interview_prep_assistant_with_history():
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "A good STAR answer should emphasize how you resolved database locking."
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    payload = {
        "message": "Can you refine my answer to the database lock question?",
        "history": [
            {"role": "user", "content": "How do I answer a behavioral question about system failure?"},
            {"role": "assistant", "content": "Structure your response using STAR: Situation, Task, Action, Result."}
        ]
    }

    with patch("routers.internships._get_groq_client", return_value=mock_client):
        response = client.post("/internships/interview-prep-assistant", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "STAR" in data["reply"]
    mock_client.chat.completions.create.assert_called_once()
