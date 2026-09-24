from datetime import datetime
from typing import List, Optional
from app.models.schemas import Ticket, Activity, Notification
from app.schemas.all_schemas import TicketOut
from app.models.enums import UserRole, TicketStatus, SLAStatus, ActivityAction, PendingReason
from app.schemas.all_schemas import (
    TicketCreate, TicketUpdate, TicketAssignRequest, TicketStatusRequest,
    TicketCommentRequest, TicketInternalNoteRequest, TicketResolveRequest,
    TicketReopenRequest, TicketEscalateRequest, PendingDetails,
    StudentDashboardOut, StaffDashboardOut, ManagerDashboardOut, StaffWorkloadItem
)
from app.repositories.ticket_repository import TicketRepository
from app.repositories.user_repository import UserRepository
from app.repositories.activity_notification_repository import (
    ActivityRepository, NotificationRepository, EscalationRepository
)
from app.services.sla_service import SLAService
from app.services.status_validator import StatusTransitionValidator
from app.services.escalation_service import EscalationService
from app.services.ai_service import AIService
from app.storage.memory import db

class TicketService:
    def __init__(
        self,
        ticket_repo: Optional[TicketRepository] = None,
        user_repo: Optional[UserRepository] = None,
        activity_repo: Optional[ActivityRepository] = None,
        notif_repo: Optional[NotificationRepository] = None,
        escalation_service: Optional[EscalationService] = None
    ):
        self.ticket_repo = ticket_repo or TicketRepository()
        self.user_repo = user_repo or UserRepository()
        self.activity_repo = activity_repo or ActivityRepository()
        self.notif_repo = notif_repo or NotificationRepository()
        self.escalation_service = escalation_service or EscalationService(
            ticket_repo=self.ticket_repo,
            activity_repo=self.activity_repo,
            notif_repo=self.notif_repo,
            user_repo=self.user_repo
        )

    def _enrich_ticket_out(self, ticket: Ticket) -> TicketOut:
        sla, ageing = SLAService.evaluate_sla_and_ageing(ticket)
        # Check automatic escalation trigger
        self.escalation_service.check_and_auto_escalate(ticket, sla.status)

        # Get latest activity timestamp
        activities = self.activity_repo.get_by_ticket_id(ticket.id, include_internal=True)
        last_act = activities[-1].created_at if activities else ticket.updated_at

        return TicketOut(
            id=ticket.id,
            ticket_number=ticket.ticket_number,
            student_id=ticket.student_id,
            student_name=ticket.student_name,
            student_email=ticket.student_email,
            category=ticket.category,
            subject=ticket.subject,
            description=ticket.description,
            priority=ticket.priority,
            status=ticket.status,
            department=ticket.department,
            assigned_staff_id=ticket.assigned_staff_id,
            assigned_staff_name=ticket.assigned_staff_name,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            sla_due_at=ticket.sla_due_at,
            sla_status=sla.status,
            resolved_at=ticket.resolved_at,
            closed_at=ticket.closed_at,
            resolution_summary=ticket.resolution_summary,
            reopen_count=ticket.reopen_count,
            escalation_count=ticket.escalation_count,
            is_escalated=ticket.is_escalated,
            pending_details=ticket.pending_details,
            attachments=ticket.attachments,
            sla=sla,
            ageing=ageing,
            last_activity_at=last_act
        )

    def create_ticket(self, data: TicketCreate, student_user) -> TicketOut:
        now = datetime.utcnow()
        ticket_id = db.next_ticket_id()
        ticket_number = f"TKT-2026-{ticket_id:05d}"

        # Classify if priority or department omitted
        priority = data.priority
        department = data.department
        if not priority or not department:
            ai_res = AIService.classify_ticket(data.subject, data.description)
            priority = priority or ai_res.priority
            department = department or ai_res.department

        sla_due = SLAService.calculate_initial_sla_due(priority, now)

        ticket = Ticket(
            id=ticket_id,
            ticket_number=ticket_number,
            student_id=student_user.id,
            student_name=student_user.name,
            student_email=student_user.email,
            category=data.category,
            subject=data.subject,
            description=data.description,
            priority=priority,
            status=TicketStatus.NEW,
            department=department,
            assigned_staff_id=None,
            assigned_staff_name=None,
            created_at=now,
            updated_at=now,
            sla_due_at=sla_due,
            sla_status=SLAStatus.ON_TRACK,
            attachments=data.attachments or []
        )

        saved = self.ticket_repo.create(ticket)

        # Log creation activity
        self.activity_repo.create(Activity(
            id=db.next_activity_id(),
            ticket_id=ticket.id,
            actor_id=student_user.id,
            actor_name=student_user.name,
            actor_role=student_user.role,
            action=ActivityAction.TICKET_CREATED,
            description=f"Ticket #{ticket_number} created with priority {priority.value}.",
            is_internal=False,
            metadata={"category": ticket.category, "department": ticket.department}
        ))

        # Notify student
        self.notif_repo.create(Notification(
            id=db.next_notification_id(),
            user_id=student_user.id,
            ticket_id=ticket.id,
            title="Ticket Submitted",
            message=f"Your ticket #{ticket_number} has been submitted successfully.",
            event_type="TICKET_CREATED"
        ))

        # Notify department managers
        managers = self.user_repo.get_all(role=UserRole.MANAGER, department=department)
        for m in managers:
            self.notif_repo.create(Notification(
                id=db.next_notification_id(),
                user_id=m.id,
                ticket_id=ticket.id,
                title="New Ticket in Department",
                message=f"New ticket #{ticket_number} ({priority.value}) waiting for assignment.",
                event_type="TICKET_CREATED"
            ))

        return self._enrich_ticket_out(saved)

    def get_ticket(self, ticket_id: int, current_user) -> TicketOut:
        ticket = self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        # Object-level authorization: Students cannot see other students' tickets
        if current_user.role == UserRole.STUDENT and ticket.student_id != current_user.id:
            raise PermissionError("Access denied: You can only view your own tickets.")

        return self._enrich_ticket_out(ticket)

    def list_tickets(
        self,
        current_user,
        department: Optional[str] = None,
        status: Optional[TicketStatus] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        assigned_staff_id: Optional[int] = None
    ) -> List[TicketOut]:
        student_filter = None
        dept_filter = department
        staff_filter = assigned_staff_id

        if current_user.role == UserRole.STUDENT:
            student_filter = current_user.id
            dept_filter = None
            staff_filter = None
        elif current_user.role == UserRole.STAFF:
            # Staff by default see assigned tickets or department tickets if specified
            if assigned_staff_id is None and not department:
                staff_filter = current_user.id
        elif current_user.role == UserRole.MANAGER:
            # Managers by default see their department tickets unless specified
            if not dept_filter and current_user.department:
                dept_filter = current_user.department

        raw_tickets = self.ticket_repo.get_all(
            student_id=student_filter,
            assigned_staff_id=staff_filter,
            department=dept_filter,
            status=status,
            priority=priority,
            category=category,
            search=search
        )

        return [self._enrich_ticket_out(t) for t in raw_tickets]

    def assign_ticket(self, ticket_id: int, req: TicketAssignRequest, current_user) -> TicketOut:
        # Authorization check: only manager or admin or self-assign by staff
        if current_user.role not in [UserRole.MANAGER, UserRole.ADMIN, UserRole.STAFF]:
            raise PermissionError("Unauthorized to assign tickets")

        ticket = self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        staff = self.user_repo.get_by_id(req.staff_id)
        if not staff or staff.role not in [UserRole.STAFF, UserRole.MANAGER]:
            raise ValueError("Target user is not a valid staff member")

        if not staff.is_active:
            raise ValueError("Cannot assign to an inactive staff member")

        is_reassign = ticket.assigned_staff_id is not None
        ticket.assigned_staff_id = staff.id
        ticket.assigned_staff_name = staff.name

        # If it was NEW, transition to ASSIGNED
        if ticket.status == TicketStatus.NEW:
            ticket.status = TicketStatus.ASSIGNED

        ticket.updated_at = datetime.utcnow()
        self.ticket_repo.update(ticket)

        action_type = ActivityAction.TICKET_REASSIGNED if is_reassign else ActivityAction.TICKET_ASSIGNED
        self.activity_repo.create(Activity(
            id=db.next_activity_id(),
            ticket_id=ticket.id,
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            action=action_type,
            description=f"Ticket assigned to {staff.name}.",
            is_internal=False,
            metadata={"assigned_staff_id": staff.id}
        ))

        # Notify staff
        self.notif_repo.create(Notification(
            id=db.next_notification_id(),
            user_id=staff.id,
            ticket_id=ticket.id,
            title="Ticket Assigned to You",
            message=f"You have been assigned to Ticket #{ticket.ticket_number}.",
            event_type="ASSIGNMENT"
        ))

        return self._enrich_ticket_out(ticket)

    def change_status(self, ticket_id: int, req: TicketStatusRequest, current_user) -> TicketOut:
        ticket = self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        valid, err = StatusTransitionValidator.validate_transition(
            current_status=ticket.status,
            target_status=req.status,
            user_role=current_user.role,
            is_owner=(ticket.student_id == current_user.id)
        )
        if not valid:
            raise ValueError(err)

        old_status = ticket.status
        ticket.status = req.status
        now = datetime.utcnow()

        # Handle Pause/Unpause SLA for WAITING_FOR_STUDENT
        if req.status == TicketStatus.WAITING_FOR_STUDENT:
            ticket.paused_at = now
            reason = req.pending_reason or PendingReason.WAITING_FOR_STUDENT
            action = req.requested_action or "Awaiting student response or information."
            ticket.pending_details = PendingDetails(
                reason=reason,
                since=now,
                requested_action=action,
                requested_by=current_user.name
            )
        else:
            if old_status == TicketStatus.WAITING_FOR_STUDENT and ticket.paused_at:
                pause_duration = (now - ticket.paused_at).total_seconds()
                ticket.total_paused_seconds += int(pause_duration)
                ticket.paused_at = None
                ticket.pending_details = None

        ticket.updated_at = now
        self.ticket_repo.update(ticket)

        # Activity log
        desc = f"Status changed from {old_status.value} to {req.status.value}."
        if req.comment:
            desc += f" Note: {req.comment}"

        self.activity_repo.create(Activity(
            id=db.next_activity_id(),
            ticket_id=ticket.id,
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            action=ActivityAction.STATUS_CHANGED,
            description=desc,
            is_internal=False,
            metadata={"old_status": old_status.value, "new_status": req.status.value}
        ))

        # Notify student of status update
        self.notif_repo.create(Notification(
            id=db.next_notification_id(),
            user_id=ticket.student_id,
            ticket_id=ticket.id,
            title="Ticket Status Updated",
            message=f"Ticket #{ticket.ticket_number} status updated to {req.status.value}.",
            event_type="STATUS_CHANGED"
        ))

        return self._enrich_ticket_out(ticket)

    def add_comment(self, ticket_id: int, req: TicketCommentRequest, current_user) -> Activity:
        ticket = self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        # Authorization check
        if current_user.role == UserRole.STUDENT and ticket.student_id != current_user.id:
            raise PermissionError("Access denied")

        if ticket.status == TicketStatus.CLOSED:
            raise ValueError("Cannot comment on a closed ticket.")

        now = datetime.utcnow()
        action_type = ActivityAction.STUDENT_REPLIED if current_user.role == UserRole.STUDENT else ActivityAction.STAFF_REPLIED

        activity = Activity(
            id=db.next_activity_id(),
            ticket_id=ticket.id,
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            action=action_type,
            description=req.comment,
            is_internal=False,
            created_at=now
        )
        self.activity_repo.create(activity)

        # If student replied and ticket was in WAITING_FOR_STUDENT, transition to IN_PROGRESS!
        if current_user.role == UserRole.STUDENT and ticket.status == TicketStatus.WAITING_FOR_STUDENT:
            if ticket.paused_at:
                ticket.total_paused_seconds += int((now - ticket.paused_at).total_seconds())
                ticket.paused_at = None
            ticket.status = TicketStatus.IN_PROGRESS
            ticket.pending_details = None
            ticket.updated_at = now
            self.ticket_repo.update(ticket)

            self.activity_repo.create(Activity(
                id=db.next_activity_id(),
                ticket_id=ticket.id,
                actor_id=current_user.id,
                actor_name=current_user.name,
                actor_role=current_user.role,
                action=ActivityAction.STATUS_CHANGED,
                description="Status automatically changed to IN_PROGRESS upon student reply.",
                is_internal=False,
                metadata={"reason": "student_response"}
            ))

            if ticket.assigned_staff_id:
                self.notif_repo.create(Notification(
                    id=db.next_notification_id(),
                    user_id=ticket.assigned_staff_id,
                    ticket_id=ticket.id,
                    title="Student Responded",
                    message=f"Student replied to Ticket #{ticket.ticket_number}. Moved to IN_PROGRESS.",
                    event_type="STUDENT_REPLIED"
                ))
        elif current_user.role != UserRole.STUDENT:
            # Notify student of staff response
            self.notif_repo.create(Notification(
                id=db.next_notification_id(),
                user_id=ticket.student_id,
                ticket_id=ticket.id,
                title="Support Update",
                message=f"Staff replied on Ticket #{ticket.ticket_number}.",
                event_type="STAFF_REPLIED"
            ))

        ticket.updated_at = now
        self.ticket_repo.update(ticket)
        return activity

    def add_internal_note(self, ticket_id: int, req: TicketInternalNoteRequest, current_user) -> Activity:
        if current_user.role == UserRole.STUDENT:
            raise PermissionError("Students cannot create or view internal notes.")

        ticket = self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        activity = Activity(
            id=db.next_activity_id(),
            ticket_id=ticket.id,
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            action=ActivityAction.INTERNAL_NOTE_ADDED,
            description=req.note,
            is_internal=True,
            created_at=datetime.utcnow()
        )
        self.activity_repo.create(activity)
        ticket.updated_at = datetime.utcnow()
        self.ticket_repo.update(ticket)
        return activity

    def resolve_ticket(self, ticket_id: int, req: TicketResolveRequest, current_user) -> TicketOut:
        if current_user.role == UserRole.STUDENT:
            raise PermissionError("Only staff and managers can resolve tickets.")

        ticket = self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        valid, err = StatusTransitionValidator.validate_transition(
            current_status=ticket.status,
            target_status=TicketStatus.RESOLVED,
            user_role=current_user.role
        )
        if not valid:
            raise ValueError(err)

        now = datetime.utcnow()
        ticket.status = TicketStatus.RESOLVED
        ticket.resolved_at = now
        ticket.resolution_summary = req.resolution_summary
        ticket.pending_details = None
        ticket.updated_at = now
        self.ticket_repo.update(ticket)

        self.activity_repo.create(Activity(
            id=db.next_activity_id(),
            ticket_id=ticket.id,
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            action=ActivityAction.TICKET_RESOLVED,
            description=f"Ticket marked as RESOLVED. Resolution: {req.resolution_summary}",
            is_internal=False,
            metadata={"summary": req.resolution_summary}
        ))

        # Notify student
        self.notif_repo.create(Notification(
            id=db.next_notification_id(),
            user_id=ticket.student_id,
            ticket_id=ticket.id,
            title="Ticket Resolved",
            message=f"Ticket #{ticket.ticket_number} has been resolved. You can review or reopen if needed.",
            event_type="TICKET_RESOLVED"
        ))

        return self._enrich_ticket_out(ticket)

    def reopen_ticket(self, ticket_id: int, req: TicketReopenRequest, current_user) -> TicketOut:
        ticket = self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        if current_user.role == UserRole.STUDENT and ticket.student_id != current_user.id:
            raise PermissionError("Access denied")

        valid, err = StatusTransitionValidator.validate_transition(
            current_status=ticket.status,
            target_status=TicketStatus.REOPENED,
            user_role=current_user.role,
            is_owner=(ticket.student_id == current_user.id)
        )
        if not valid:
            raise ValueError(err)

        now = datetime.utcnow()
        ticket.status = TicketStatus.REOPENED
        ticket.reopen_count += 1
        ticket.resolved_at = None
        ticket.updated_at = now
        self.ticket_repo.update(ticket)

        self.activity_repo.create(Activity(
            id=db.next_activity_id(),
            ticket_id=ticket.id,
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_role=current_user.role,
            action=ActivityAction.TICKET_REOPENED,
            description=f"Ticket reopened by {current_user.name}. Reason: {req.reason}",
            is_internal=False,
            metadata={"reason": req.reason, "reopen_count": ticket.reopen_count}
        ))

        # Check if reopen threshold triggered escalation
        sla, _ = SLAService.evaluate_sla_and_ageing(ticket)
        self.escalation_service.check_and_auto_escalate(ticket, sla.status)

        # Notify assigned staff
        if ticket.assigned_staff_id:
            self.notif_repo.create(Notification(
                id=db.next_notification_id(),
                user_id=ticket.assigned_staff_id,
                ticket_id=ticket.id,
                title="Ticket Reopened",
                message=f"Ticket #{ticket.ticket_number} was reopened by {current_user.name}.",
                event_type="TICKET_REOPENED"
            ))

        return self._enrich_ticket_out(ticket)

    def escalate_ticket(self, ticket_id: int, req: TicketEscalateRequest, current_user) -> TicketOut:
        if current_user.role not in [UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]:
            raise PermissionError("Students cannot escalate tickets.")

        ticket = self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        new_owner_name = None
        if req.target_staff_id:
            target = self.user_repo.get_by_id(req.target_staff_id)
            if target:
                new_owner_name = target.name

        self.escalation_service.perform_escalation(
            ticket=ticket,
            reason=req.reason,
            new_owner_id=req.target_staff_id,
            new_owner_name=new_owner_name,
            notes=req.notes,
            actor_name=current_user.name,
            actor_role=current_user.role,
            actor_id=current_user.id
        )

        return self._enrich_ticket_out(ticket)

    def get_activities(self, ticket_id: int, current_user) -> List[Activity]:
        ticket = self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        if current_user.role == UserRole.STUDENT and ticket.student_id != current_user.id:
            raise PermissionError("Access denied")

        include_internal = (current_user.role != UserRole.STUDENT)
        return self.activity_repo.get_by_ticket_id(ticket_id, include_internal=include_internal)

    # Dashboards
    def get_student_dashboard(self, current_user) -> StudentDashboardOut:
        user_tickets = self.ticket_repo.get_all(student_id=current_user.id)
        open_count = len([t for t in user_tickets if t.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]])
        in_prog = len([t for t in user_tickets if t.status in [TicketStatus.IN_PROGRESS, TicketStatus.ASSIGNED]])
        waiting = len([t for t in user_tickets if t.status == TicketStatus.WAITING_FOR_STUDENT])
        resolved = len([t for t in user_tickets if t.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]])

        recent = [self._enrich_ticket_out(t) for t in user_tickets[:6]]

        return StudentDashboardOut(
            my_open_tickets=open_count,
            in_progress=in_prog,
            waiting_for_response=waiting,
            resolved=resolved,
            recent_tickets=recent
        )

    def get_staff_dashboard(self, current_user) -> StaffDashboardOut:
        all_tickets = self.ticket_repo.get_all()
        my_tickets = [t for t in all_tickets if t.assigned_staff_id == current_user.id]

        open_mine = [t for t in my_tickets if t.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]]
        
        # Calculate SLA metrics for staff
        due_soon_count = 0
        breached_count = 0
        waiting_count = len([t for t in open_mine if t.status == TicketStatus.WAITING_FOR_STUDENT])

        for t in open_mine:
            sla, _ = SLAService.evaluate_sla_and_ageing(t)
            if sla.status == SLAStatus.AT_RISK:
                due_soon_count += 1
            elif sla.status == SLAStatus.BREACHED:
                breached_count += 1

        # Priority distribution across my open tickets
        prio_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "URGENT": 0}
        for t in open_mine:
            prio_dist[t.priority.value] = prio_dist.get(t.priority.value, 0) + 1

        # Workload calculation across all staff in the same department
        dept_staff = self.user_repo.get_all(role=UserRole.STAFF, department=current_user.department)
        workload = []
        for s in dept_staff:
            s_open = [t for t in all_tickets if t.assigned_staff_id == s.id and t.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]]
            s_breached = 0
            for t in s_open:
                sla, _ = SLAService.evaluate_sla_and_ageing(t)
                if sla.status == SLAStatus.BREACHED:
                    s_breached += 1
            workload.append(StaffWorkloadItem(
                staff_id=s.id,
                name=s.name,
                active_tickets=len(s_open),
                breached_tickets=s_breached
            ))

        # Oldest tickets
        oldest = sorted(open_mine, key=lambda x: x.created_at)[:5]
        recent = sorted(open_mine, key=lambda x: x.updated_at, reverse=True)[:5]

        return StaffDashboardOut(
            my_open_tickets=len(open_mine),
            due_soon=due_soon_count,
            sla_breached=breached_count,
            waiting_for_student=waiting_count,
            workload=workload,
            priority_distribution=prio_dist,
            oldest_tickets=[self._enrich_ticket_out(t) for t in oldest],
            recently_assigned=[self._enrich_ticket_out(t) for t in recent]
        )

    def get_manager_dashboard(self, current_user) -> ManagerDashboardOut:
        all_tickets = self.ticket_repo.get_all()
        # If manager has department, filter by department, unless ADMIN
        if current_user.role == UserRole.MANAGER and current_user.department:
            relevant = [t for t in all_tickets if t.department == current_user.department]
        else:
            relevant = all_tickets

        open_tickets = [t for t in relevant if t.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]]
        unassigned = [t for t in open_tickets if t.assigned_staff_id is None]
        escalated = [t for t in open_tickets if t.is_escalated]

        at_risk_count = 0
        breached_count = 0
        category_dist = {}
        prio_dist = {}
        status_dist = {}
        ageing_dist = {"0-1 day": 0, "1-3 days": 0, "3-7 days": 0, "7-14 days": 0, "14+ days": 0}

        for t in relevant:
            status_dist[t.status.value] = status_dist.get(t.status.value, 0) + 1
            category_dist[t.category] = category_dist.get(t.category, 0) + 1
            prio_dist[t.priority.value] = prio_dist.get(t.priority.value, 0) + 1

        for t in open_tickets:
            sla, ageing = SLAService.evaluate_sla_and_ageing(t)
            if sla.status == SLAStatus.AT_RISK:
                at_risk_count += 1
            elif sla.status == SLAStatus.BREACHED:
                breached_count += 1
            ageing_dist[ageing.bucket] = ageing_dist.get(ageing.bucket, 0) + 1

        # Average resolution time
        resolved_tickets = [t for t in relevant if t.resolved_at is not None]
        total_res_hours = 0.0
        if resolved_tickets:
            for t in resolved_tickets:
                diff_hours = (t.resolved_at - t.created_at).total_seconds() / 3600.0
                total_res_hours += max(0.1, diff_hours)
            avg_hours = round(total_res_hours / len(resolved_tickets), 1)
        else:
            avg_hours = 0.0

        # Workload across all staff
        staff_members = self.user_repo.get_all(role=UserRole.STAFF)
        if current_user.role == UserRole.MANAGER and current_user.department:
            staff_members = [s for s in staff_members if s.department == current_user.department]

        workload = []
        for s in staff_members:
            s_open = [t for t in all_tickets if t.assigned_staff_id == s.id and t.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]]
            s_breached = 0
            for t in s_open:
                sla, _ = SLAService.evaluate_sla_and_ageing(t)
                if sla.status == SLAStatus.BREACHED:
                    s_breached += 1
            workload.append(StaffWorkloadItem(
                staff_id=s.id,
                name=s.name,
                active_tickets=len(s_open),
                breached_tickets=s_breached
            ))

        oldest = sorted(open_tickets, key=lambda x: x.created_at)[:6]

        return ManagerDashboardOut(
            total_open=len(open_tickets),
            unassigned=len(unassigned),
            sla_at_risk=at_risk_count,
            sla_breached=breached_count,
            escalated=len(escalated),
            avg_resolution_hours=avg_hours,
            tickets_by_category=category_dist,
            tickets_by_priority=prio_dist,
            tickets_by_status=status_dist,
            staff_workload=workload,
            ageing_distribution=ageing_dist,
            oldest_unresolved_tickets=[self._enrich_ticket_out(t) for t in oldest]
        )
