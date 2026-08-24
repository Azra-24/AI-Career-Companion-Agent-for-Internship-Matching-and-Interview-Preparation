from fastapi.testclient import TestClient
from resume_parser.app import app
import pytest

client = TestClient(app)


def test_apply_and_get_applications_flow():
    # 1. Clear or initialize memory store by making calls
    payload = {
        "user_email": "test_applicant@example.com",
        "internship_id": "software-engineering-intern",
        "internship_title": "Software Engineering Intern",
        "company": "Google",
        "required_skills": ["Python", "Go", "Docker"],
        "candidate_skills": ["Python", "SQL", "Git"]
    }
    
    # Post application
    response = client.post("/internships/apply", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "id" in data
    assert data["user_email"] == "test_applicant@example.com"
    assert data["internship_title"] == "Software Engineering Intern"
    assert data["company"] == "Google"
    assert data["status"] == "Screening"
    
    # Readiness score should be 1 matched skill (Python) / 3 required * 100 = 33.333%
    assert 33.0 <= data["readiness_score"] <= 34.0
    assert data["matched_skills"] == ["Python"]
    assert "Docker" in data["missing_skills"]
    assert "Go" in data["missing_skills"]
    
    # Verify stages structure
    assert len(data["application_stages"]) == 5
    assert data["application_stages"][0]["stage"] == "Resume Submitted"
    assert data["application_stages"][0]["status"] == "Completed"
    assert data["application_stages"][1]["status"] == "In Progress"
    
    # Verify learning plan recommendations exist for the 2 missing skills
    assert len(data["learning_recommendations"]) >= 2
    
    # 2. Get applications (all)
    get_res = client.get("/internships/applications")
    assert get_res.status_code == 200
    apps = get_res.json()
    assert len(apps) >= 1
    assert any(a["id"] == data["id"] for a in apps)
    
    # 3. Get applications (filtered by email)
    filtered_res = client.get("/internships/applications?email=test_applicant@example.com")
    assert filtered_res.status_code == 200
    filtered_apps = filtered_res.json()
    assert len(filtered_apps) >= 1
    assert all(a["user_email"] == "test_applicant@example.com" for a in filtered_apps)
