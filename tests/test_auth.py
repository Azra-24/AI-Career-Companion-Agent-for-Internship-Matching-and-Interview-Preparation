import pytest
import uuid
from fastapi.testclient import TestClient
from resume_parser.app import app

def test_auth_register_login_me_flow():
    with TestClient(app) as client:
        # Generate unique email for registration
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        reg_payload = {
            "full_name": "Test User",
            "email": unique_email,
            "password": "SecurePassword123"
        }
        
        # 1. Register a new user
        response = client.post("/auth/register", json=reg_payload)
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["full_name"] == "Test User"
        assert data["user"]["email"] == unique_email

        token = data["access_token"]

        # 2. Try registering the same user again (should fail with 400)
        response_dup = client.post("/auth/register", json=reg_payload)
        assert response_dup.status_code == 400

        # 3. Log in with the registered user
        login_payload = {
            "email": unique_email,
            "password": "SecurePassword123"
        }
        response_login = client.post("/auth/login", json=login_payload)
        assert response_login.status_code == 200
        login_data = response_login.json()
        assert "access_token" in login_data
        assert login_data["user"]["email"] == unique_email

        # 4. Access protected /auth/me
        response_me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response_me.status_code == 200
        me_data = response_me.json()
        assert me_data["full_name"] == "Test User"
        assert me_data["email"] == unique_email

        # 5. Access /auth/me with invalid token
        response_me_invalid = client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert response_me_invalid.status_code == 401
