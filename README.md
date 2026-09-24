# EduSupport — Student Support & Ticket Management System

EduSupport is a full-stack, enterprise-grade student support and administrative inquiry tracking platform engineered for universities and educational institutions.

> **IMPORTANT ARCHITECTURAL NOTE**:
> This platform strictly uses **in-memory Python data structures** in accordance with evaluation constraints. **No databases (PostgreSQL, MySQL, SQLite, MongoDB, Firebase, Supabase) or ORMs (SQLAlchemy, Prisma) are used.**
> The system implements a clean **Repository & Service Pattern**, ensuring the storage layer can be seamlessly replaced with a real database in the future.

---

## 🌟 Key Features

1. **Role-Based Workflows & Dashboards**:
   - **Student**: Submit tickets, track SLA countdown, view responses, upload supporting documents, reopen eligible resolved tickets.
   - **Staff**: Process assigned tickets, request additional documents, add internal notes (hidden from students), resolve tickets.
   - **Manager**: Department-level oversight, reassign staff, track workload distribution, SLA breach monitoring, manual & automated escalations.
   - **Admin**: Campus-wide analytics, comprehensive oversight across all 5 departments.

2. **Strict Finite-State Ticket Lifecycle**:
   - `NEW` &rarr; `ASSIGNED` &rarr; `IN_PROGRESS` &rarr; `WAITING_FOR_STUDENT` &rarr; `RESOLVED` &rarr; `CLOSED`
   - Allowed Reopen: `RESOLVED` &rarr; `REOPENED` &rarr; `IN_PROGRESS`
   - Centralized status transition validator rejects illegal state transitions.

3. **Dynamic SLA & Ageing Engine**:
   - Priority-based SLAs:
     - `LOW`: 72 hours
     - `MEDIUM`: 48 hours
     - `HIGH`: 24 hours
     - `URGENT`: 8 hours
   - **Dynamic SLA statuses**: `ON_TRACK`, `AT_RISK` (< 25% time remaining), `BREACHED`, `PAUSED`.
   - **SLA Pausing**: When tickets enter `WAITING_FOR_STUDENT`, the SLA timer pauses automatically.
   - **Ageing Buckets**: `0–1 day`, `1–3 days`, `3–7 days`, `7–14 days`, `14+ days`.

4. **Escalation Engine**:
   - Triggers when:
     - SLA is breached.
     - Urgent ticket SLA is approaching limit.
     - Ticket age exceeds 14 days.
     - Ticket is repeatedly reopened (&ge; 2 times).
   - Prevents duplicate escalations and logs full reassignment audit history.

5. **Activity Timeline & Commenting**:
   - Public replies visible to students and staff.
   - Internal notes with lock indicator visible only to Staff, Managers, and Admins.
   - Complete audit trail of state transitions, assignments, and escalations.

6. **Optional AI Ticket Classification with Fallback**:
   - Endpoint: `POST /ai/classify-ticket`
   - Classifies category, priority, department, and summary based on request text.
   - If AI or network fails, built-in deterministic heuristic fallback ensures zero failure.

---

## 🏗️ Project Architecture

```text
EduQuery/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI entrypoint + lifespan startup
│   │   ├── core/
│   │   │   ├── config.py               # Application settings
│   │   │   └── security.py             # PBKDF2-SHA256 & JWT authentication
│   │   ├── models/
│   │   │   ├── enums.py                # Enums (UserRole, TicketStatus, Priority, SLAStatus)
│   │   │   └── schemas.py              # Domain Pydantic models
│   │   ├── schemas/
│   │   │   └── all_schemas.py          # DTO schemas for API request/response
│   │   ├── storage/
│   │   │   ├── memory.py               # Singleton in-memory collections
│   │   │   └── seed.py                 # Startup seed data (41 users, 55+ tickets)
│   │   ├── repositories/
│   │   │   ├── user_repository.py      # Abstracted user storage access
│   │   │   ├── ticket_repository.py    # Abstracted ticket query & filter access
│   │   │   └── activity_notification_repository.py
│   │   ├── services/
│   │   │   ├── ticket_service.py       # Core lifecycle logic & aggregations
│   │   │   ├── sla_service.py          # Dynamic SLA & ageing calculations
│   │   │   ├── escalation_service.py   # Automated escalation logic
│   │   │   ├── status_validator.py     # State machine validation
│   │   │   └── ai_service.py           # Intelligent classification + fallback
│   │   └── api/v1/
│   │       ├── auth.py                 # Login, me, staff directory
│   │       ├── tickets.py              # CRUD, lifecycle, notes, comments
│   │       └── dashboards.py           # Student, staff, manager dashboards
│   ├── tests/
│   │   └── test_backend.py             # Full test suite (100% pass)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/                 # Badges, Notifications, etc.
│   │   ├── context/                    # AuthContext with 1-click role switcher
│   │   ├── layouts/                    # MainLayout (sidebar, nav)
│   │   ├── pages/                      # Login, Dashboard, Queue, Details, Create
│   │   ├── services/                   # Axios API client
│   │   └── types/                      # TypeScript domain definitions
│   └── vite.config.ts
├── SUBMISSION_AND_AI_REPORT.md         # Official Walk-in Drive submission report
└── README.md
```

---

## ⚡ Quick Start Instructions

### 1. Start Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 2. Start Frontend

```bash
cd frontend
npm run preview
# or npm run dev
```
- Frontend Web App: [http://127.0.0.1:5173](http://127.0.0.1:5173)

---

## 🔑 Demo Credentials

All seed accounts use the default password: **`password123`**

| Role | Name | Email | Focus / Department |
| :--- | :--- | :--- | :--- |
| **Admin** | System Administrator | `admin@institution.edu` | Campus-Wide Oversight |
| **Manager** | Dr. Sarah Jenkins | `manager.finance@institution.edu` | Finance Department |
| **Manager** | Prof. David Chen | `manager.records@institution.edu` | Registrar & Student Records |
| **Staff** | Michael Scott | `staff.finance1@institution.edu` | Finance Operations |
| **Staff** | Jim Halpert | `staff.records1@institution.edu` | Records Operations |
| **Student** | Aarav Sharma | `aarav.sharma@student.institution.edu` | Student View |
| **Student** | Diya Patel | `diya.patel@student.institution.edu` | Student View |

> *Tip: The frontend includes a **Quick Demo Switcher** in both the Login page and the left navigation sidebar to switch between roles instantly.*

---

## 🧪 Automated Testing

Run the test suite with:

```bash
cd backend
$env:PYTHONPATH="."
pytest tests/test_backend.py -v
```

Tests cover:
- Health check & seed data integrity
- JWT authentication & `/auth/me`
- **Student ticket isolation** (403 Forbidden on foreign ticket access)
- Full ticket lifecycle (`NEW` &rarr; `ASSIGNED` &rarr; `IN_PROGRESS` &rarr; `WAITING_FOR_STUDENT` &rarr; Student reply &rarr; `IN_PROGRESS` &rarr; `RESOLVED` &rarr; `REOPENED`)
- Invalid status transition enforcement
- AI classification fallback resilience
