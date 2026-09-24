from typing import Tuple, Optional
from app.models.enums import TicketStatus, ALLOWED_TRANSITIONS, UserRole

class StatusTransitionValidator:
    @staticmethod
    def validate_transition(
        current_status: TicketStatus,
        target_status: TicketStatus,
        user_role: UserRole,
        is_owner: bool = False
    ) -> Tuple[bool, Optional[str]]:
        # Check if terminal
        if current_status == TicketStatus.CLOSED:
            return False, "Cannot transition a CLOSED ticket. Closed tickets are terminal."

        # Reopen validation
        if target_status == TicketStatus.REOPENED:
            if current_status != TicketStatus.RESOLVED:
                return False, f"Only tickets in RESOLVED status can be reopened (current: {current_status.value})."
            # Students and admins/managers can reopen
            if user_role not in [UserRole.STUDENT, UserRole.MANAGER, UserRole.ADMIN]:
                return False, "Only the student or management can reopen a ticket."
            return True, None

        # Check allowed transitions map
        allowed = ALLOWED_TRANSITIONS.get(current_status, [])
        if target_status not in allowed:
            allowed_names = [s.value for s in allowed]
            return False, f"Invalid status transition from {current_status.value} to {target_status.value}. Allowed: {allowed_names}"

        # Role-based constraints
        if user_role == UserRole.STUDENT:
            # Student can only transition to IN_PROGRESS (by responding) or REOPENED
            if target_status not in [TicketStatus.IN_PROGRESS, TicketStatus.REOPENED]:
                return False, f"Students cannot directly transition ticket to {target_status.value}."

        if target_status == TicketStatus.CLOSED:
            # Only staff, manager, or admin can close ticket
            if user_role not in [UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]:
                return False, "Only staff or administration can close a ticket."

        return True, None
