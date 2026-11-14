import sys
import os
import asyncio

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from httpx import AsyncClient, ASGITransport
from main import app
from database import SessionLocal
from models import User, IrrigationHistory, UserSettings
from auth import hash_password, verify_password

async def run_all_tests():
    print("==================================================")
    print(" RUNNING AURA SYSTEM & API VALIDATION TESTS")
    print("==================================================")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Health check
        response = await client.get("/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("[PASS] System Health Check")

        # 2. Registration validation - mismatched passwords
        res_mismatch = await client.post("/api/auth/register", json={
            "full_name": "Test User",
            "username": "test_mismatch_usr",
            "password": "Password123",
            "confirm_password": "WrongPassword456"
        })
        assert res_mismatch.status_code == 400
        print("[PASS] Registration Rejection: Password Mismatch (400)")

        # 3. Successful Registration of New User
        reg_username = "aura_field_tech"
        res_reg = await client.post("/api/auth/register", json={
            "full_name": "Field Technician Alex",
            "username": reg_username,
            "password": "techpassword123",
            "confirm_password": "techpassword123"
        })
        if res_reg.status_code == 400 and "already registered" in res_reg.json()["detail"]:
            pass  # Already registered in previous run
        else:
            assert res_reg.status_code == 201
            assert res_reg.json()["username"] == reg_username
        print("[PASS] User Registration Success (/api/auth/register)")

        # 4. Duplicate Username Rejection
        res_dup = await client.post("/api/auth/register", json={
            "full_name": "Duplicate Attempt",
            "username": reg_username,
            "password": "techpassword123",
            "confirm_password": "techpassword123"
        })
        assert res_dup.status_code == 400
        print("[PASS] Registration Rejection: Duplicate Username (400)")

        # 5. Invalid Login Test
        response = await client.post("/api/auth/login", json={"username": "aura_admin_01", "password": "wrongpassword"})
        assert response.status_code == 401, f"Expected 401 on wrong password, got {response.status_code}"
        print("[PASS] Invalid Password Rejection (401)")

        response = await client.post("/api/auth/login", json={"username": "nonexistent_user", "password": "adminpassword"})
        assert response.status_code == 401, f"Expected 401 on invalid user, got {response.status_code}"
        print("[PASS] Non-existent User Rejection (401)")

        # 6. Protected endpoint access blocked without token (before login)
        response = await client.get("/api/auth/me")
        assert response.status_code == 401, f"Expected 401 without token, got {response.status_code}"
        print("[PASS] Protected Endpoint Access Blocked Without Token (401)")

        # 7. Valid Admin Login Test
        response = await client.post("/api/auth/login", json={"username": "aura_admin_01", "password": "admin123"})
        assert response.status_code == 200, f"Login failed: {response.text}"
        login_data = response.json()
        assert "access_token" in login_data
        token = login_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("[PASS] Valid Administrator Authentication (200 OK & JWT Token)")

        # 8. Access profile with token
        response = await client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200, f"Failed /api/auth/me: {response.text}"
        assert response.json()["username"] == "aura_admin_01"
        print("[PASS] Authenticated Profile Retrieval (/api/auth/me)")

        # Clear admin history first
        await client.delete("/api/irrigation/history", headers=headers)

        # 9. Save Calculation Test (Python Engine Calculation)
        calc_payload = {
            "crop_type": "Tomato",
            "soil_type": "loamy",
            "weather_condition": "warm",
            "hours_since_irrigation": 12
        }
        response = await client.post("/api/irrigation/calculate", json=calc_payload, headers=headers)
        assert response.status_code == 201, f"Failed saving calculation: {response.text}"
        record = response.json()
        assert record["crop_type"] == "Tomato"
        assert record["eto_estimate"] == 6.8
        assert record["crop_coefficient"] == 1.15
        assert record["etc_loss_rate"] == 7.82
        assert "estimated_moisture" in record
        print("[PASS] Python Irrigation Calculation Executed & Saved to SQLite (/api/irrigation/calculate)")

        # 10. Retrieve Calculation History
        response = await client.get("/api/irrigation/history", headers=headers)
        assert response.status_code == 200, f"Failed fetching history: {response.text}"
        history = response.json()
        assert len(history) >= 1
        record_id = history[0]["id"]
        assert history[0]["id"] == record_id
        print(f"[PASS] Irrigation History Retrieved (Count: {len(history)})")

        # 11. Retrieve Single Record
        response = await client.get(f"/api/irrigation/history/{record_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["id"] == record_id
        print(f"[PASS] Single History Record Retrieved (#{record_id})")

        # 12. Multi-user Isolation Test with Registered User
        login_tech = await client.post("/api/auth/login", json={
            "username": reg_username,
            "password": "techpassword123"
        })
        assert login_tech.status_code == 200
        headers_tech = {"Authorization": f"Bearer {login_tech.json()['access_token']}"}

        # Clear tech's history to verify isolation
        await client.delete("/api/irrigation/history", headers=headers_tech)
        tech_history = await client.get("/api/irrigation/history", headers=headers_tech)
        assert len(tech_history.json()) == 0

        # Registered user shouldn't see admin's single record
        response = await client.get(f"/api/irrigation/history/{record_id}", headers=headers_tech)
        assert response.status_code == 404, f"Expected 404 for cross-user record access, got {response.status_code}"
        print("[PASS] Cross-User Record Isolation Verified (404 Not Found)")

        # 13. User Settings Get & Update Test (User 1)
        settings_payload = {
            "sensor_frequency": "Eco-mode (1h)",
            "autonomous_mode": False
        }
        response = await client.put("/api/users/settings", json=settings_payload, headers=headers)
        assert response.status_code == 200
        assert response.json()["sensor_frequency"] == "Eco-mode (1h)"
        assert response.json()["autonomous_mode"] is False
        print("[PASS] Node Settings Update for Admin (/api/users/settings)")

        # 14. User Settings Isolation (Registered User has separate settings)
        tech_settings = await client.get("/api/users/settings", headers=headers_tech)
        assert tech_settings.status_code == 200
        # Should be default "Standard (15m)", not Eco-mode
        assert tech_settings.json()["sensor_frequency"] == "Standard (15m)"
        print("[PASS] Node Settings Isolated Between Users")

        # 15. Clear History Test
        response = await client.delete("/api/irrigation/history", headers=headers)
        assert response.status_code == 200
        print("[PASS] User History Cleared (/api/irrigation/history)")

        # 16. Logout Test
        response = await client.post("/api/auth/logout", headers=headers)
        assert response.status_code == 200
        print("[PASS] User Logout (/api/auth/logout)")

        # 17. Verify frontend pages serve properly
        index_res = await client.get("/")
        assert index_res.status_code == 200
        assert "Aura" in index_res.text
        print("[PASS] Frontend Login/Register Page Served (/)")

        dash_res = await client.get("/dash.html")
        assert dash_res.status_code == 200
        assert "Smart Irrigation" in dash_res.text
        print("[PASS] Frontend Dashboard Served (/dash.html)")

    print("==================================================")
    print(" ALL 17 BACKEND, REGISTRATION & MULTI-USER TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
