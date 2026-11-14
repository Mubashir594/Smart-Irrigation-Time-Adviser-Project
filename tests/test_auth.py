import pytest
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from httpx import AsyncClient, ASGITransport
from main import app
from auth import hash_password, verify_password

@pytest.mark.asyncio
async def test_password_hashing():
    """Verify bcrypt password hashing and verification functionality."""
    plain = "secure_test_password_123"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong_password", hashed) is False

@pytest.mark.asyncio
async def test_user_registration_pipeline():
    """Verify registration, password matching validation, and duplicate rejection."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Reject registration with mismatched passwords
        mismatch_payload = {
            "full_name": "Test Mismatch",
            "username": "mismatch_user_01",
            "password": "Password123",
            "confirm_password": "DifferentPassword456"
        }
        res_mismatch = await client.post("/api/auth/register", json=mismatch_payload)
        assert res_mismatch.status_code == 400
        assert "Passwords do not match" in res_mismatch.json()["detail"]

        # 2. Successful registration of a new user
        reg_payload = {
            "full_name": "Dr. Sarah Mitchell",
            "username": "sarah_mitchell",
            "password": "sarahpassword123",
            "confirm_password": "sarahpassword123"
        }
        # In case the user exists from previous test run, handle idempotently or clean
        res_reg = await client.post("/api/auth/register", json=reg_payload)
        if res_reg.status_code == 400 and "already registered" in res_reg.json()["detail"]:
            pass  # Already registered
        else:
            assert res_reg.status_code == 201
            data = res_reg.json()
            assert data["username"] == "sarah_mitchell"
            assert data["full_name"] == "Dr. Sarah Mitchell"

        # 3. Reject duplicate username registration
        res_dup = await client.post("/api/auth/register", json=reg_payload)
        assert res_dup.status_code == 400
        assert "already registered" in res_dup.json()["detail"]

        # 4. Successful login with newly registered credentials
        login_res = await client.post("/api/auth/login", json={
            "username": "sarah_mitchell",
            "password": "sarahpassword123"
        })
        assert login_res.status_code == 200
        login_data = login_res.json()
        assert "access_token" in login_data
        assert login_data["user"]["username"] == "sarah_mitchell"
        assert login_data["user"]["full_name"] == "Dr. Sarah Mitchell"

        # 5. Profile verification with JWT
        headers = {"Authorization": f"Bearer {login_data['access_token']}"}
        res_me = await client.get("/api/auth/me", headers=headers)
        assert res_me.status_code == 200
        assert res_me.json()["username"] == "sarah_mitchell"
        assert res_me.json()["full_name"] == "Dr. Sarah Mitchell"

        # 6. Reject invalid login credentials
        res_fail = await client.post("/api/auth/login", json={
            "username": "sarah_mitchell",
            "password": "wrongpassword"
        })
        assert res_fail.status_code == 401

        # 7. Verify original administrator account still works
        admin_login = await client.post("/api/auth/login", json={
            "username": "aura_admin_01",
            "password": "admin123"
        })
        assert admin_login.status_code == 200
        assert admin_login.json()["user"]["username"] == "aura_admin_01"

        # 8. Logout
        res_logout = await client.post("/api/auth/logout", headers=headers)
        assert res_logout.status_code == 200

if __name__ == "__main__":
    pytest.main(["-v", __file__])
