from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import User
from app.models.enums import UserRole
from app.schemas.all_schemas import (
    StudentDashboardOut, StaffDashboardOut, ManagerDashboardOut,
    NotificationOut, AIClassifyRequest, AIClassifyResponse
)
from app.api.v1.auth import get_current_user, require_role
from app.services.ticket_service import TicketService
from app.services.ai_service import AIService
from app.repositories.activity_notification_repository import NotificationRepository

router = APIRouter(tags=["Dashboards & System"])
ticket_service = TicketService()
notif_repo = NotificationRepository()

# Dashboards
@router.get("/dashboard/student", response_model=StudentDashboardOut)
def get_student_dashboard(current_user: User = Depends(get_current_user)):
    return ticket_service.get_student_dashboard(current_user)

@router.get("/dashboard/staff", response_model=StaffDashboardOut)
def get_staff_dashboard(current_user: User = Depends(require_role([UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]))):
    return ticket_service.get_staff_dashboard(current_user)

@router.get("/dashboard/manager", response_model=ManagerDashboardOut)
def get_manager_dashboard(current_user: User = Depends(require_role([UserRole.MANAGER, UserRole.ADMIN]))):
    return ticket_service.get_manager_dashboard(current_user)

# Notifications
@router.get("/notifications", response_model=List[NotificationOut])
def get_notifications(current_user: User = Depends(get_current_user)):
    notifs = notif_repo.get_by_user_id(current_user.id)
    return [
        NotificationOut(
            id=n.id,
            user_id=n.user_id,
            ticket_id=n.ticket_id,
            title=n.title,
            message=n.message,
            is_read=n.is_read,
            event_type=n.event_type,
            created_at=n.created_at
        )
        for n in notifs
    ]

@router.patch("/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(notification_id: int, current_user: User = Depends(get_current_user)):
    n = notif_repo.mark_as_read(notification_id, current_user.id)
    if not n:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return NotificationOut(
        id=n.id,
        user_id=n.user_id,
        ticket_id=n.ticket_id,
        title=n.title,
        message=n.message,
        is_read=n.is_read,
        event_type=n.event_type,
        created_at=n.created_at
    )

@router.post("/notifications/mark-all-read")
def mark_all_notifications_read(current_user: User = Depends(get_current_user)):
    notif_repo.mark_all_read(current_user.id)
    return {"status": "ok"}

# AI Classification
@router.post("/ai/classify-ticket", response_model=AIClassifyResponse)
def classify_ticket(req: AIClassifyRequest):
    try:
        return AIService.classify_ticket(req.subject, req.description)
    except Exception:
        # Guaranteed fallback
        return AIClassifyResponse(
            category="General Administration",
            priority="MEDIUM",
            department="Campus Administration",
            summary=req.subject[:100],
            confidence=0.5,
            source="rule_based_fallback"
        )
