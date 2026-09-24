from datetime import datetime
from typing import Optional
from app.models.schemas import Ticket, Escalation
from app.models.enums import Priority, TicketStatus, SLAStatus, ActivityAction, UserRole
from app.repositories.ticket_repository import TicketRepository
from app.repositories.activity_notification_repository import (
    ActivityRepository, NotificationRepository, EscalationRepository
)
from app.repositories.user_repository import UserRepository
from app.models.schemas import Activity, Notification
from app.storage.memory import db

class EscalationService:
    def __init__(
        self,
        ticket_repo: Optional[TicketRepository] = None,
        activity_repo: Optional[ActivityRepository] = None,
        notif_repo: Optional[NotificationRepository] = None,
        escalation_repo: Optional[EscalationRepository] = None,
        user_repo: Optional[UserRepository] = None
    ):
        self.ticket_repo = ticket_repo or TicketRepository()
        self.activity_repo = activity_repo or ActivityRepository()
        self.notif_repo = notif_repo or NotificationRepository()
        self.escalation_repo = escalation_repo or EscalationRepository()
        self.user_repo = user_repo or UserRepository()

    def check_and_auto_escalate(self, ticket: Ticket, sla_status: SLAStatus) -> bool:
        """
        Escalate when:
        1. SLA is breached
        2. SLA is approaching for an URGENT ticket
        3. Ageing exceeds 14 days
        4. Ticket is repeatedly reopened (reopen_count >= 2)
        Prevent duplicate escalations (e.g. if already escalated for same trigger)
        """
        if ticket.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            return False

        if ticket.is_escalated:
            return False  # Prevent duplicate escalation

        reason = None
        if sla_status == SLAStatus.BREACHED:
            reason = "SLA_BREACH"
        elif ticket.priority == Priority.URGENT and sla_status == SLAStatus.AT_RISK:
            reason = "URGENT_SLA_APPROACHING"
        elif ticket.reopen_count >= 2:
            reason = "REPEATEDLY_REOPENED"
        else:
            age_days = (datetime.utcnow() - ticket.created_at).total_seconds() / 86400
            if age_days >= 14:
                reason = "EXCEEDED_AGEING_THRESHOLD_14D"

        if not reason:
            return False

        # Find department manager or general manager to escalate to
        managers = self.user_repo.get_all(role=UserRole.MANAGER, department=ticket.department)
        if not managers:
            managers = self.user_repo.get_all(role=UserRole.MANAGER)
        
        manager = managers[0] if managers else None
        manager_id = manager.id if manager else None
        manager_name = manager.name if manager else "Department Management"

        return self.perform_escalation(
            ticket=ticket,
            reason=reason,
            new_owner_id=manager_id,
            new_owner_name=manager_name,
            notes=f"Automatic system escalation triggered due to {reason}."
        )

    def perform_escalation(
        self,
        ticket: Ticket,
        reason: str,
        new_owner_id: Optional[int] = None,
        new_owner_name: Optional[str] = None,
        notes: Optional[str] = None,
        actor_name: str = "System Escalation Engine",
        actor_role: UserRole = UserRole.ADMIN,
        actor_id: int = 1
    ) -> bool:
        prev_owner_id = ticket.assigned_staff_id
        prev_owner_name = ticket.assigned_staff_name

        ticket.is_escalated = True
        ticket.escalation_count += 1
        if new_owner_id:
            ticket.assigned_staff_id = new_owner_id
            ticket.assigned_staff_name = new_owner_name
        ticket.updated_at = datetime.utcnow()
        self.ticket_repo.update(ticket)

        escalation = Escalation(
            id=db.next_escalation_id(),
            ticket_id=ticket.id,
            reason=reason,
            previous_owner_id=prev_owner_id,
            previous_owner_name=prev_owner_name,
            new_owner_id=new_owner_id,
            new_owner_name=new_owner_name,
            notes=notes,
            created_at=datetime.utcnow()
        )
        self.escalation_repo.create(escalation)

        # Activity log
        activity = Activity(
            id=db.next_activity_id(),
            ticket_id=ticket.id,
            actor_id=actor_id,
            actor_name=actor_name,
            actor_role=actor_role,
            action=ActivityAction.TICKET_ESCALATED,
            description=f"Ticket escalated. Reason: {reason}. Assigned to: {new_owner_name or 'Management'}.",
            is_internal=False,
            metadata={"reason": reason, "previous_owner": prev_owner_id, "new_owner": new_owner_id}
        )
        self.activity_repo.create(activity)

        # Notify new owner and previous owner
        if new_owner_id:
            self.notif_repo.create(Notification(
                id=db.next_notification_id(),
                user_id=new_owner_id,
                ticket_id=ticket.id,
                title="Ticket Escalated to You",
                message=f"Ticket #{ticket.ticket_number} was escalated ({reason}).",
                event_type="ESCALATION"
            ))

        if prev_owner_id and prev_owner_id != new_owner_id:
            self.notif_repo.create(Notification(
                id=db.next_notification_id(),
                user_id=prev_owner_id,
                ticket_id=ticket.id,
                title="Ticket Escalated",
                message=f"Ticket #{ticket.ticket_number} previously assigned to you was escalated.",
                event_type="ESCALATION"
            ))

        return True
