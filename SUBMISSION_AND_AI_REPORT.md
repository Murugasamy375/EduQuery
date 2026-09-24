

## 1. Executive Summary & Problem Understanding

Educational institutions handle high volumes of student queries spanning fees, attendance condonation, ID smartcard malfunctions, certificates, and general administrative services. In typical college settings:
- Student inquiries get buried in decentralized email inboxes or paper applications.
- Response SLAs breach without visibility, leading to student distress and escalated complaints.
- Staff workloads are unevenly distributed without real-time visibility across departments.
- Statuses are reduced to binary flags (`pending=True`) rather than meaningful domain workflows (`WAITING_FOR_STUDENT`, `WAITING_FOR_DOCUMENT`).

**EduSupport** addresses these institutional operational challenges by providing a full-stack, SLA-driven ticket management platform tailored for Students, Staff members, Department Managers, and Campus Administrators.

---

## 2. Product Thinking & Core Assumptions

1. **Zero Database Constraint & In-Memory Data Structures**:
   - The application strictly operates on Python in-memory data structures (`tickets = []`, `users = []`, `activities = []`, `notifications = []`, `escalations = []`, `sla_policies = []`).
   - Clean Repository & Service architecture was implemented to completely decouple storage from domain business logic, allowing trivial migration to PostgreSQL/SQLAlchemy in production.
2. **Explicit Actionable Pending States**:
   - Rather than a generic status, explicit pending workflows (`WAITING_FOR_STUDENT`, `WAITING_FOR_STAFF`, `WAITING_FOR_DEPARTMENT`, `WAITING_FOR_DOCUMENT`) record exact reasons, timestamps, and requested student actions.
   - When in `WAITING_FOR_STUDENT`, the SLA timer **automatically pauses**, preventing staff penalties while waiting for the student to upload evidence.
3. **Automatic Resumption on Student Reply**:
   - When a student responds to a ticket in `WAITING_FOR_STUDENT`, the status automatically flips to `IN_PROGRESS` and the SLA clock resumes.
4. **SLA & Dynamic Ageing Engine**:
   - Remaining SLA time and Ageing buckets (`0-1 day`, `1-3 days`, `3-7 days`, `7-14 days`, `14+ days`) are **never stored permanently**; they are dynamically calculated from creation, pause, and resolution timestamps.
5. **Auditable Activity Timeline & Internal Notes**:
   - Internal staff observations are protected by role-based filtering (`is_internal=True`), completely hidden from student views.

---

## 3. Architecture & Technical Design

### Backend Architecture (FastAPI + Pydantic)
```text
backend/
├── app/
│   ├── main.py                     # FastAPI app with lifespan seed startup & CORS
│   ├── core/
│   │   ├── config.py               # App configuration & JWT settings
│   │   └── security.py             # PBKDF2-SHA256 password hashing & JWT tokens
│   ├── models/
│   │   ├── enums.py                # Enums (UserRole, TicketStatus, Priority, SLAStatus)
│   │   └── schemas.py              # Domain Pydantic entities
│   ├── schemas/
│   │   └── all_schemas.py          # Request/response validation & serialization schemas
│   ├── storage/
│   │   ├── memory.py               # Singleton in-memory storage manager
│   │   └── seed.py                 # Realistic seed data (41 users, 55+ tickets)
│   ├── repositories/
│   │   ├── user_repository.py      # Abstracted user data access
│   │   ├── ticket_repository.py    # Abstracted ticket data access & filters
│   │   └── activity_notification_repository.py # Activity, notification & escalation logs
│   └── services/
│       ├── ticket_service.py       # Full lifecycle, RBAC & dashboard aggregations
│       ├── sla_service.py          # Dynamic SLA evaluation & ageing bucket engine
│       ├── escalation_service.py   # Automated breach & repeat-reopen escalation
│       ├── status_validator.py     # Centralized finite-state transition validator
│       └── ai_service.py           # Classification engine with zero-failure fallback
└── tests/
    └── test_backend.py             # Comprehensive automated test suite
```

### Frontend Architecture (React 19 + TypeScript + Vite + Tailwind CSS)
- **Role-Tailored Dashboards**: Custom metrics for Student (Open, In Progress, Action Needed, Resolved), Staff (Assigned to Me, Due Soon, SLA Breached, Waiting Student), and Manager (Total Open, Unassigned, SLA At Risk, SLA Breached, Escalated, Avg Resolution Time, Team Workload).
- **Fast Demo Role Switcher**: Top-level switcher allowing immediate testing as Admin, Manager, Staff, or Student without manual relogging.
- **Dynamic SLA Badges**: Visual indicators (On Track, At Risk [amber], Breached [rose], Paused [slate]).

---

## 4. Validation & Edge Cases Handled

1. **Student Ticket Isolation**: A student querying `/tickets/{id}` belonging to another student receives `403 Forbidden`.
2. **Invalid Status Transitions**: Arbitrary status jumps (e.g. `NEW -> RESOLVED` or modifying `CLOSED` tickets) are rejected by `StatusTransitionValidator`.
3. **Reopening Closed Tickets**: Closed tickets are terminal; attempting to reopen yields an explicit error. Only `RESOLVED` tickets can be reopened.
4. **Duplicate Escalation Prevention**: Escalation engine verifies `is_escalated` state before triggering automatic escalations on SLA breach or age limits.
5. **Zero AI Point-of-Failure**: If an external LLM API is unavailable, the rule-based classification heuristics immediately provide deterministic category, department, and priority routing.
6. **Inactive Staff Assignment**: Assigning to deactivated accounts is validated and prevented.
7. **Cross-Department Restricted Visibility**: Staff only manage tickets assigned to their department or queue.

---

## 5. Mandatory AI Usage Report

### AI TOOL USED:
**Google Antigravity (Gemini 3.8 Flash)**

### WHAT I ASKED AI TO DO:
1. **Design and generate clean repository & domain service layers** for FastAPI adhering strictly to in-memory Python structures with realistic seed generation (41 users and 55+ tickets).
2. **Implement dynamic SLA calculation and finite state transition validation** enforcing allowed status transitions (`NEW -> ASSIGNED -> IN_PROGRESS -> WAITING_FOR_STUDENT -> RESOLVED -> CLOSED/REOPENED`) and pausing SLA during student waiting periods.
3. **Build the responsive React + TypeScript frontend** with Tailwind CSS, role-based dashboards, live notifications, search/filter table, and a 3-column ticket details workbench.

### PROMPT THAT WAS MOST USEFUL:
> *"Implement an SLAService and EscalationService. Calculate SLA due time, remaining time, SLA status (ON_TRACK, AT_RISK, BREACHED, PAUSED) and ageing buckets dynamically from timestamps without storing remaining time permanently. Escalate when SLA is breached, SLA is approaching for urgent tickets, or ticket is repeatedly reopened, while preventing duplicate escalations."*

### CODE GENERATED BY AI: What part?
- The backend domain models, in-memory repository abstractions, SLA calculation service (`app/services/sla_service.py`), status validator (`app/services/status_validator.py`), and realistic seed generator (`app/storage/seed.py`).
- The React frontend pages (`DashboardPage.tsx`, `TicketListPage.tsx`, `TicketDetailsPage.tsx`, `CreateTicketPage.tsx`, `LoginPage.tsx`) and layout components.

### CODE I MODIFIED: What part?
- **Authentication Hashing**: Replaced `passlib[bcrypt]` with Python's built-in `hashlib.pbkdf2_hmac` in `app/core/security.py` to eliminate bcrypt's 72-byte password limitation and backend incompatibilities on Windows.
- **Vite & Tailwind CSS v4 Configuration**: Configured `@tailwindcss/vite` plugin and updated `vite.config.ts` with API proxies.
- **TypeScript Strict Import Settings**: Adjusted `tsconfig.app.json` compiler options (`verbatimModuleSyntax: false`, `noUnusedLocals: false`) to ensure clean compilation across React 19 types.
- **Unicode Logging in FastAPI Lifespan**: Replaced unicode emoji print characters in `main.py` with standard ASCII indicators to prevent Windows CP1252 charmap encoding errors during server startup.

### AI OUTPUT THAT WAS WRONG:
1. The AI initially imported `passlib.context.CryptContext` with `bcrypt`. In newer Python/bcrypt versions on Windows, passlib triggered `ValueError: password cannot be longer than 72 bytes` and an `AttributeError: module 'bcrypt' has no attribute '__about__'`.
2. The AI initially imported `TicketOut` from `app.models.schemas` instead of `app.schemas.all_schemas`, causing an `ImportError`.
3. In `main.py`, the AI used a checkmark emoji (`\u2705`) in a console `print` statement during FastAPI lifespan startup, crashing Uvicorn under the default Windows `cp1252` console encoding.

### HOW I IDENTIFIED THE PROBLEM:
1. Ran `pytest tests/test_backend.py -v` which exposed the passlib bcrypt failure stack trace and the incorrect schema import location.
2. Ran `uvicorn app.main:app` which halted immediately with `UnicodeEncodeError: 'charmap' codec can't encode character '\u2705'`.

### HOW I FIXED IT:
1. Implemented PBKDF2-SHA256 password hashing directly using Python's standard `hashlib` and `hmac` libraries, making it 100% resilient and zero-dependency.
2. Corrected the imports in `app/services/ticket_service.py` and `app/services/sla_service.py` to import DTO schemas from `app.schemas.all_schemas`.
3. Replaced unicode emojis with `[OK]` in the startup log print statement.
4. Reran `pytest`, achieving **100% test pass rate across all 6 test suites**.

---

## 6. How to Run the Solution

### Backend:
```bash
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- API Docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`
- Run Tests: `pytest tests/test_backend.py -v`

### Frontend:
```bash
cd frontend
npm run preview
# or npm run dev
```
- Web Application: `http://127.0.0.1:5173`
- Demo Accounts:
  - **Admin**: `admin@institution.edu` / `password123`
  - **Manager (Finance)**: `manager.finance@institution.edu` / `password123`
  - **Staff**: `staff.finance1@institution.edu` / `password123`
  - **Student**: `aarav.sharma@student.institution.edu` / `password123`
