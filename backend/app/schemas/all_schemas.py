from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from app.models.enums import UserRole, TicketStatus, Priority, SLAStatus, PendingReason
from app.models.schemas import Attachment, PendingDetails

# Auth
class Token(BaseModel):
    access_token: str
    token_type: str
    user: "UserOut"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole
    department: Optional[str] = None
    student_id_card: Optional[str] = None

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    department: Optional[str] = None
    student_id_card: Optional[str] = None
    is_active: bool

# Tickets
class TicketCreate(BaseModel):
    subject: str = Field(..., min_length=5, max_length=150)
    category: str
    description: str = Field(..., min_length=10)
    priority: Optional[Priority] = None
    department: Optional[str] = None
    attachments: Optional[List[Attachment]] = Field(default_factory=list)

class TicketUpdate(BaseModel):
    subject: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    department: Optional[str] = None

class TicketAssignRequest(BaseModel):
    staff_id: int

class TicketStatusRequest(BaseModel):
    status: TicketStatus
    comment: Optional[str] = None
    # If moving to WAITING_FOR_STUDENT or pending
    pending_reason: Optional[PendingReason] = None
    requested_action: Optional[str] = None

class TicketCommentRequest(BaseModel):
    comment: str = Field(..., min_length=1)

class TicketInternalNoteRequest(BaseModel):
    note: str = Field(..., min_length=1)

class TicketResolveRequest(BaseModel):
    resolution_summary: str = Field(..., min_length=5)

class TicketReopenRequest(BaseModel):
    reason: str = Field(..., min_length=5)

class TicketEscalateRequest(BaseModel):
    reason: str = Field(..., min_length=3)
    target_staff_id: Optional[int] = None
    notes: Optional[str] = None

# SLA and Ageing Dynamic Output
class SLADisplay(BaseModel):
    status: SLAStatus
    is_breached: bool
    is_at_risk: bool
    is_paused: bool
    remaining_seconds: int
    overdue_seconds: int
    display_text: str  # e.g. "SLA: 05h 32m remaining" or "SLA BREACHED: 2h 14m overdue"
    due_at: datetime

class AgeingDisplay(BaseModel):
    age_seconds: int
    age_display: str  # e.g. "2 days 4 hours"
    bucket: str       # "0-1 day", "1-3 days", "3-7 days", "7-14 days", "14+ days"

class TicketOut(BaseModel):
    id: int
    ticket_number: str
    student_id: int
    student_name: str
    student_email: str
    category: str
    subject: str
    description: str
    priority: Priority
    status: TicketStatus
    department: str
    assigned_staff_id: Optional[int] = None
    assigned_staff_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    sla_due_at: datetime
    sla_status: SLAStatus
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    resolution_summary: Optional[str] = None
    reopen_count: int
    escalation_count: int
    is_escalated: bool
    pending_details: Optional[PendingDetails] = None
    attachments: List[Attachment] = Field(default_factory=list)
    # Computed Dynamic Fields
    sla: SLADisplay
    ageing: AgeingDisplay
    last_activity_at: Optional[datetime] = None

# Activities
class ActivityOut(BaseModel):
    id: int
    ticket_id: int
    actor_id: int
    actor_name: str
    actor_role: UserRole
    action: str
    description: str
    is_internal: bool
    metadata: Dict[str, Any]
    created_at: datetime

# Notifications
class NotificationOut(BaseModel):
    id: int
    user_id: int
    ticket_id: Optional[int]
    title: str
    message: str
    is_read: bool
    event_type: str
    created_at: datetime

# AI
class AIClassifyRequest(BaseModel):
    subject: str
    description: str

class AIClassifyResponse(BaseModel):
    category: str
    priority: Priority
    department: str
    summary: str
    confidence: float = 0.95
    source: str = "ai_engine" # or "rule_based_fallback"

# Dashboards
class StudentDashboardOut(BaseModel):
    my_open_tickets: int
    in_progress: int
    waiting_for_response: int
    resolved: int
    recent_tickets: List[TicketOut]

class StaffWorkloadItem(BaseModel):
    staff_id: int
    name: str
    active_tickets: int
    breached_tickets: int

class StaffDashboardOut(BaseModel):
    my_open_tickets: int
    due_soon: int
    sla_breached: int
    waiting_for_student: int
    workload: List[StaffWorkloadItem]
    priority_distribution: Dict[str, int]
    oldest_tickets: List[TicketOut]
    recently_assigned: List[TicketOut]

class ManagerDashboardOut(BaseModel):
    total_open: int
    unassigned: int
    sla_at_risk: int
    sla_breached: int
    escalated: int
    avg_resolution_hours: float
    tickets_by_category: Dict[str, int]
    tickets_by_priority: Dict[str, int]
    tickets_by_status: Dict[str, int]
    staff_workload: List[StaffWorkloadItem]
    ageing_distribution: Dict[str, int]
    oldest_unresolved_tickets: List[TicketOut]
