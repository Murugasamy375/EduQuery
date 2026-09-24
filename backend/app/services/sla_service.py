from datetime import datetime, timedelta
from typing import Tuple
from app.models.schemas import Ticket
from app.schemas.all_schemas import SLADisplay, AgeingDisplay
from app.models.enums import Priority, SLAStatus, TicketStatus, DEFAULT_SLA_HOURS

class SLAService:
    @staticmethod
    def calculate_initial_sla_due(priority: Priority, created_at: datetime) -> datetime:
        hours = DEFAULT_SLA_HOURS.get(priority, 48)
        return created_at + timedelta(hours=hours)

    @staticmethod
    def evaluate_sla_and_ageing(ticket: Ticket, now: datetime = None) -> Tuple[SLADisplay, AgeingDisplay]:
        if now is None:
            now = datetime.utcnow()

        # Age calculation
        # If closed or resolved, age stops at that point, else up to now
        end_time = ticket.closed_at or ticket.resolved_at or now
        age_delta = max(timedelta(seconds=0), end_time - ticket.created_at)
        age_seconds = int(age_delta.total_seconds())

        days = age_seconds // 86400
        hours = (age_seconds % 86400) // 3600
        mins = (age_seconds % 3600) // 60

        if days > 0:
            age_display = f"{days}d {hours}h"
        elif hours > 0:
            age_display = f"{hours}h {mins}m"
        else:
            age_display = f"{mins}m"

        # Ageing bucket
        if days < 1:
            bucket = "0-1 day"
        elif days < 3:
            bucket = "1-3 days"
        elif days < 7:
            bucket = "3-7 days"
        elif days < 14:
            bucket = "7-14 days"
        else:
            bucket = "14+ days"

        ageing = AgeingDisplay(
            age_seconds=age_seconds,
            age_display=age_display,
            bucket=bucket
        )

        # SLA calculation
        # If paused (e.g. WAITING_FOR_STUDENT)
        is_paused = ticket.status == TicketStatus.WAITING_FOR_STUDENT
        # Adjust effective due_at if paused
        effective_due_at = ticket.sla_due_at + timedelta(seconds=ticket.total_paused_seconds)
        if is_paused and ticket.paused_at:
            current_pause_duration = (now - ticket.paused_at).total_seconds()
            effective_due_at += timedelta(seconds=max(0, current_pause_duration))

        # Check resolution status
        if ticket.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            # Evaluated at resolved_at time
            eval_time = ticket.resolved_at or ticket.closed_at or now
            if eval_time > effective_due_at:
                overdue = int((eval_time - effective_due_at).total_seconds())
                sla_status = SLAStatus.BREACHED
                display_text = f"SLA BREACHED ({overdue // 3600}h {(overdue % 3600) // 60}m overdue at resolution)"
                return SLADisplay(
                    status=sla_status,
                    is_breached=True,
                    is_at_risk=False,
                    is_paused=False,
                    remaining_seconds=0,
                    overdue_seconds=overdue,
                    display_text=display_text,
                    due_at=effective_due_at
                ), ageing
            else:
                return SLADisplay(
                    status=SLAStatus.ON_TRACK,
                    is_breached=False,
                    is_at_risk=False,
                    is_paused=False,
                    remaining_seconds=0,
                    overdue_seconds=0,
                    display_text="Resolved within SLA",
                    due_at=effective_due_at
                ), ageing

        if is_paused:
            diff = (effective_due_at - now).total_seconds()
            rem = max(0, int(diff))
            return SLADisplay(
                status=SLAStatus.PAUSED,
                is_breached=False,
                is_at_risk=False,
                is_paused=True,
                remaining_seconds=rem,
                overdue_seconds=0,
                display_text=f"PAUSED ({rem // 3600:02d}h {(rem % 3600) // 60:02d}m remaining)",
                due_at=effective_due_at
            ), ageing

        time_diff = (effective_due_at - now).total_seconds()
        total_sla_seconds = DEFAULT_SLA_HOURS.get(ticket.priority, 48) * 3600

        if time_diff <= 0:
            overdue_seconds = int(abs(time_diff))
            overdue_h = overdue_seconds // 3600
            overdue_m = (overdue_seconds % 3600) // 60
            sla_status = SLAStatus.BREACHED
            display_text = f"SLA BREACHED: {overdue_h}h {overdue_m:02d}m overdue"
            return SLADisplay(
                status=sla_status,
                is_breached=True,
                is_at_risk=False,
                is_paused=False,
                remaining_seconds=0,
                overdue_seconds=overdue_seconds,
                display_text=display_text,
                due_at=effective_due_at
            ), ageing
        else:
            remaining_seconds = int(time_diff)
            rem_h = remaining_seconds // 3600
            rem_m = (remaining_seconds % 3600) // 60

            # If less than 25% time remains (or under 4 hours), mark AT_RISK
            fraction_remaining = time_diff / max(1, total_sla_seconds)
            is_at_risk = fraction_remaining <= 0.25 or (ticket.priority == Priority.URGENT and remaining_seconds <= 7200)

            sla_status = SLAStatus.AT_RISK if is_at_risk else SLAStatus.ON_TRACK
            status_prefix = "SLA AT RISK" if is_at_risk else "SLA"
            display_text = f"{status_prefix}: {rem_h:02d}h {rem_m:02d}m remaining"

            return SLADisplay(
                status=sla_status,
                is_breached=False,
                is_at_risk=is_at_risk,
                is_paused=False,
                remaining_seconds=remaining_seconds,
                overdue_seconds=0,
                display_text=display_text,
                due_at=effective_due_at
            ), ageing
