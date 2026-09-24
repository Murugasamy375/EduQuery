import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.storage.memory import db
from app.storage.seed import seed_database
from app.models.enums import UserRole, TicketStatus

client = TestClient(app)

@pytest.fixture(autouse=True)
def init_db():
    seed_database(db)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["users_count"] >= 35
    assert data["tickets_count"] >= 50

def test_login_and_auth():
    # Login admin
    res = client.post("/auth/login", json={"email": "admin@institution.edu", "password": "password123"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    assert token is not None

    # Check /auth/me
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "admin@institution.edu"
    assert me_res.json()["role"] == "ADMIN"

def test_student_ticket_isolation():
    # Login student 1 (Aarav Sharma)
    res1 = client.post("/auth/login", json={"email": "aarav.sharma@student.institution.edu", "password": "password123"})
    token1 = res1.json()["access_token"]
    user1_id = res1.json()["user"]["id"]

    # Student 1 creates ticket
    create_res = client.post("/tickets", json={
        "subject": "Need my bonafide certificate for education loan",
        "category": "Certificates",
        "description": "Please issue bonafide certificate addressed to State Bank of India."
    }, headers={"Authorization": f"Bearer {token1}"})
    assert create_res.status_code == 201
    ticket_id = create_res.json()["id"]

    # Login student 2 (Diya Patel)
    res2 = client.post("/auth/login", json={"email": "diya.patel@student.institution.edu", "password": "password123"})
    token2 = res2.json()["access_token"]

    # Student 2 tries to view Student 1's ticket -> MUST RETURN 403 FORBIDDEN
    forbidden_res = client.get(f"/tickets/{ticket_id}", headers={"Authorization": f"Bearer {token2}"})
    assert forbidden_res.status_code == 403

def test_full_lifecycle_and_transition_validator():
    # Login student
    res_s = client.post("/auth/login", json={"email": "aarav.sharma@student.institution.edu", "password": "password123"})
    s_token = res_s.json()["access_token"]

    # 1. Create Ticket
    t_res = client.post("/tickets", json={
        "subject": "Biometric scanner error at library turnstile",
        "category": "ID Card",
        "description": "RFID turnstile does not open when scanned."
    }, headers={"Authorization": f"Bearer {s_token}"})
    assert t_res.status_code == 201
    t_data = t_res.json()
    t_id = t_data["id"]
    assert t_data["status"] == "NEW"

    # Login Manager
    res_m = client.post("/auth/login", json={"email": "manager.records@institution.edu", "password": "password123"})
    m_token = res_m.json()["access_token"]

    # 2. Assign Ticket to Staff (Jim Halpert - records1)
    staff_user = next(u for u in db.users if u.email == "staff.records1@institution.edu")
    assign_res = client.post(f"/tickets/{t_id}/assign", json={"staff_id": staff_user.id}, headers={"Authorization": f"Bearer {m_token}"})
    assert assign_res.status_code == 200
    assert assign_res.json()["status"] == "ASSIGNED"

    # Login Staff Jim
    res_staff = client.post("/auth/login", json={"email": "staff.records1@institution.edu", "password": "password123"})
    staff_token = res_staff.json()["access_token"]

    # 3. Staff moves ticket to IN_PROGRESS
    prog_res = client.post(f"/tickets/{t_id}/status", json={"status": "IN_PROGRESS"}, headers={"Authorization": f"Bearer {staff_token}"})
    assert prog_res.status_code == 200
    assert prog_res.json()["status"] == "IN_PROGRESS"

    # 4. Staff moves ticket to WAITING_FOR_STUDENT (Pause SLA)
    wait_res = client.post(f"/tickets/{t_id}/status", json={
        "status": "WAITING_FOR_STUDENT",
        "pending_reason": "WAITING_FOR_DOCUMENT",
        "requested_action": "Please provide your student ID card barcode number."
    }, headers={"Authorization": f"Bearer {staff_token}"})
    assert wait_res.status_code == 200
    assert wait_res.json()["status"] == "WAITING_FOR_STUDENT"
    assert wait_res.json()["sla"]["is_paused"] is True

    # 5. Student replies -> Automatically moves back to IN_PROGRESS
    reply_res = client.post(f"/tickets/{t_id}/comments", json={"comment": "My barcode number is 987654321."}, headers={"Authorization": f"Bearer {s_token}"})
    assert reply_res.status_code == 200
    
    # Check ticket status is now IN_PROGRESS
    t_after_reply = client.get(f"/tickets/{t_id}", headers={"Authorization": f"Bearer {s_token}"}).json()
    assert t_after_reply["status"] == "IN_PROGRESS"

    # 6. Staff resolves ticket
    res_res = client.post(f"/tickets/{t_id}/resolve", json={"resolution_summary": "Re-encoded RFID chip on smartcard."}, headers={"Authorization": f"Bearer {staff_token}"})
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "RESOLVED"

    # 7. Student can reopen resolved ticket
    reopen_res = client.post(f"/tickets/{t_id}/reopen", json={"reason": "Still not opening at Gate 2."}, headers={"Authorization": f"Bearer {s_token}"})
    assert reopen_res.status_code == 200
    assert reopen_res.json()["status"] == "REOPENED"

def test_invalid_status_transition():
    # Login student
    res_s = client.post("/auth/login", json={"email": "aarav.sharma@student.institution.edu", "password": "password123"})
    s_token = res_s.json()["access_token"]
    
    t_res = client.post("/tickets", json={
        "subject": "Test invalid status jumping",
        "category": "General Administration",
        "description": "Testing that random status jump fails"
    }, headers={"Authorization": f"Bearer {s_token}"})
    t_id = t_res.json()["id"]

    # Student tries to jump straight from NEW to RESOLVED -> 400 or 403
    bad_res = client.post(f"/tickets/{t_id}/status", json={"status": "RESOLVED"}, headers={"Authorization": f"Bearer {s_token}"})
    assert bad_res.status_code in [400, 403]

def test_ai_classification_fallback():
    res = client.post("/ai/classify-ticket", json={
        "subject": "My tuition fee receipt is not generated",
        "description": "Paid fee through netbanking but status shows pending payment."
    })
    assert res.status_code == 200
    data = res.json()
    assert data["category"] == "Fees"
    assert data["department"] == "Finance"
    assert "priority" in data
