from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.schemas import User, Activity
from app.models.enums import UserRole, TicketStatus, Priority
from app.schemas.all_schemas import (
    TicketCreate, TicketUpdate, TicketOut, TicketAssignRequest, TicketStatusRequest,
    TicketCommentRequest, TicketInternalNoteRequest, TicketResolveRequest,
    TicketReopenRequest, TicketEscalateRequest, ActivityOut
)
from app.api.v1.auth import get_current_user, require_role
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/tickets", tags=["Tickets"])
ticket_service = TicketService()

@router.get("", response_model=List[TicketOut])
def list_tickets(
    department: Optional[str] = None,
    status: Optional[TicketStatus] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    assigned_staff_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    return ticket_service.list_tickets(
        current_user=current_user,
        department=department,
        status=status,
        priority=priority,
        category=category,
        search=search,
        assigned_staff_id=assigned_staff_id
    )

@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    req: TicketCreate,
    current_user: User = Depends(get_current_user)
):
    try:
        return ticket_service.create_ticket(req, current_user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user)
):
    try:
        return ticket_service.get_ticket(ticket_id, current_user)
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))

@router.post("/{ticket_id}/assign", response_model=TicketOut)
def assign_ticket(
    ticket_id: int,
    req: TicketAssignRequest,
    current_user: User = Depends(require_role([UserRole.MANAGER, UserRole.ADMIN, UserRole.STAFF]))
):
    try:
        return ticket_service.assign_ticket(ticket_id, req, current_user)
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

@router.post("/{ticket_id}/status", response_model=TicketOut)
def update_status(
    ticket_id: int,
    req: TicketStatusRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        return ticket_service.change_status(ticket_id, req, current_user)
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

@router.post("/{ticket_id}/comments", response_model=ActivityOut)
def add_comment(
    ticket_id: int,
    req: TicketCommentRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        act = ticket_service.add_comment(ticket_id, req, current_user)
        return ActivityOut(
            id=act.id,
            ticket_id=act.ticket_id,
            actor_id=act.actor_id,
            actor_name=act.actor_name,
            actor_role=act.actor_role,
            action=act.action,
            description=act.description,
            is_internal=act.is_internal,
            metadata=act.metadata,
            created_at=act.created_at
        )
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

@router.post("/{ticket_id}/internal-note", response_model=ActivityOut)
def add_internal_note(
    ticket_id: int,
    req: TicketInternalNoteRequest,
    current_user: User = Depends(require_role([UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]))
):
    try:
        act = ticket_service.add_internal_note(ticket_id, req, current_user)
        return ActivityOut(
            id=act.id,
            ticket_id=act.ticket_id,
            actor_id=act.actor_id,
            actor_name=act.actor_name,
            actor_role=act.actor_role,
            action=act.action,
            description=act.description,
            is_internal=act.is_internal,
            metadata=act.metadata,
            created_at=act.created_at
        )
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

@router.post("/{ticket_id}/resolve", response_model=TicketOut)
def resolve_ticket(
    ticket_id: int,
    req: TicketResolveRequest,
    current_user: User = Depends(require_role([UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]))
):
    try:
        return ticket_service.resolve_ticket(ticket_id, req, current_user)
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

@router.post("/{ticket_id}/reopen", response_model=TicketOut)
def reopen_ticket(
    ticket_id: int,
    req: TicketReopenRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        return ticket_service.reopen_ticket(ticket_id, req, current_user)
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

@router.post("/{ticket_id}/escalate", response_model=TicketOut)
def escalate_ticket(
    ticket_id: int,
    req: TicketEscalateRequest,
    current_user: User = Depends(require_role([UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]))
):
    try:
        return ticket_service.escalate_ticket(ticket_id, req, current_user)
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

@router.get("/{ticket_id}/activities", response_model=List[ActivityOut])
def get_ticket_activities(
    ticket_id: int,
    current_user: User = Depends(get_current_user)
):
    try:
        acts = ticket_service.get_activities(ticket_id, current_user)
        return [
            ActivityOut(
                id=a.id,
                ticket_id=a.ticket_id,
                actor_id=a.actor_id,
                actor_name=a.actor_name,
                actor_role=a.actor_role,
                action=a.action,
                description=a.description,
                is_internal=a.is_internal,
                metadata=a.metadata,
                created_at=a.created_at
            )
            for a in acts
        ]
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
