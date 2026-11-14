import pytest
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from httpx import AsyncClient, ASGITransport
from main import app
from database import SessionLocal
from models import User
from auth import hash_password

@pytest.mark.asyncio
async def test_irrigation_api_pipeline():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Authenticate admin
        login_res = await client.post("/api/auth/login", json={"username": "aura_admin_01", "password": "admin123"})
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Clear existing history first
        await client.delete("/api/irrigation/history", headers=headers)

        # 1. Post a new calculation
        calc_payload = {
            "crop_type": "Tomato",
            "soil_type": "loamy",
            "weather_condition": "warm",
            "hours_since_irrigation": 12
        }
        res_calc = await client.post("/api/irrigation/calculate", json=calc_payload, headers=headers)
        assert res_calc.status_code == 201
        data = res_calc.json()
        assert data["crop_type"] == "Tomato"
        assert data["eto_estimate"] == 6.8
        assert data["crop_coefficient"] == 1.15
        assert data["etc_loss_rate"] == 7.82
        assert "estimated_moisture" in data
        assert "irrigation_status" in data
        assert "recommendation" in data

        # 2. Retrieve History for User 1
        res_hist = await client.get("/api/irrigation/history", headers=headers)
        assert res_hist.status_code == 200
        history_list = res_hist.json()
        assert len(history_list) == 1
        record_id = history_list[0]["id"]
        assert history_list[0]["crop_type"] == "Tomato"
        assert history_list[0]["eto_estimate"] == 6.8

        # 3. Retrieve Single Record
        res_single = await client.get(f"/api/irrigation/history/{record_id}", headers=headers)
        assert res_single.status_code == 200
        assert res_single.json()["id"] == record_id

        # 4. Multi-user isolation test
        # Ensure a secondary operator exists
        db = SessionLocal()
        try:
            op2 = db.query(User).filter(User.username == "aura_operator_secondary").first()
            if not op2:
                op2 = User(full_name="Secondary Field Operator", username="aura_operator_secondary", password_hash=hash_password("operatorpass456"))
                db.add(op2)
                db.commit()
                db.refresh(op2)
        finally:
            db.close()

        # Login as operator 2
        login_op2 = await client.post("/api/auth/login", json={"username": "aura_operator_secondary", "password": "operatorpass456"})
        assert login_op2.status_code == 200
        token_op2 = login_op2.json()["access_token"]
        headers_op2 = {"Authorization": f"Bearer {token_op2}"}

        # Clear operator 2's history to ensure isolation test
        await client.delete("/api/irrigation/history", headers=headers_op2)

        # Operator 2's history should be empty (cannot see User 1's history)
        res_hist_op2 = await client.get("/api/irrigation/history", headers=headers_op2)
        assert len(res_hist_op2.json()) == 0

        # Operator 2 attempting to view User 1's single record should receive 404 Not Found
        res_cross = await client.get(f"/api/irrigation/history/{record_id}", headers=headers_op2)
        assert res_cross.status_code == 404

        # 5. User 1 Settings API
        update_payload_u1 = {
            "sensor_frequency": "Real-time (5s)",
            "autonomous_mode": False
        }
        res_update_u1 = await client.put("/api/users/settings", json=update_payload_u1, headers=headers)
        assert res_update_u1.status_code == 200
        assert res_update_u1.json()["sensor_frequency"] == "Real-time (5s)"
        assert res_update_u1.json()["autonomous_mode"] is False

        # 6. User 2 Settings Isolation (Must be separate from User 1)
        update_payload_u2 = {
            "sensor_frequency": "Eco-mode (1h)",
            "autonomous_mode": True
        }
        res_update_u2 = await client.put("/api/users/settings", json=update_payload_u2, headers=headers_op2)
        assert res_update_u2.status_code == 200
        assert res_update_u2.json()["sensor_frequency"] == "Eco-mode (1h)"
        assert res_update_u2.json()["autonomous_mode"] is True

        # Verify User 1's settings were NOT changed by User 2
        res_check_u1 = await client.get("/api/users/settings", headers=headers)
        assert res_check_u1.json()["sensor_frequency"] == "Real-time (5s)"
        assert res_check_u1.json()["autonomous_mode"] is False

        # 7. Clear History for User 1
        res_del = await client.delete("/api/irrigation/history", headers=headers)
        assert res_del.status_code == 200

        res_empty = await client.get("/api/irrigation/history", headers=headers)
        assert len(res_empty.json()) == 0

if __name__ == "__main__":
    pytest.main(["-v", __file__])
