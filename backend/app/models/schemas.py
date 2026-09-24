from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from app.models.enums import (
    UserRole, TicketStatus, Priority, SLAStatus, PendingReason
)

class User(BaseModel):
    id: int
    name: str
    email: EmailStr
    hashed_password: str
    role: UserRole
    department: Optional[str] = None
    student_id_card: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Attachment(BaseModel):
    id: str
    filename: str
    file_type: str
    size_bytes: int
    data_url: Optional[str] = None  # Base64 or mock URL
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

class PendingDetails(BaseModel):
    reason: PendingReason
    since: datetime = Field(default_factory=datetime.utcnow)
    requested_action: str
    requested_by: str

class Ticket(BaseModel):
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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    sla_due_at: datetime
    sla_status: SLAStatus = SLAStatus.ON_TRACK
    paused_at: Optional[datetime] = None
    total_paused_seconds: int = 0
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    resolution_summary: Optional[str] = None
    reopen_count: int = 0
    escalation_count: int = 0
    is_escalated: bool = False
    pending_details: Optional[PendingDetails] = None
    attachments: List[Attachment] = Field(default_factory=list)

class Activity(BaseModel):
    id: int
    ticket_id: int
    actor_id: int
    actor_name: str
    actor_role: UserRole
    action: str
    description: str
    is_internal: bool = False  # internal note vs public comment/action
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Notification(BaseModel):
    id: int
    user_id: int
    ticket_id: Optional[int] = None
    title: str
    message: str
    is_read: bool = False
    event_type: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Escalation(BaseModel):
    id: int
    ticket_id: int
    reason: str
    previous_owner_id: Optional[int] = None
    previous_owner_name: Optional[str] = None
    new_owner_id: Optional[int] = None
    new_owner_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SLAPolicy(BaseModel):
    priority: Priority
    response_hours: int
    warning_threshold_percent: float = 0.75  # 75% elapsed triggers AT_RISK
