from typing import List, Optional
from datetime import datetime
from app.models.schemas import Ticket
from app.models.enums import TicketStatus, Priority
from app.storage.memory import db

class TicketRepository:
    def __init__(self, storage=db):
        self.storage = storage

    def get_by_id(self, ticket_id: int) -> Optional[Ticket]:
        return next((t for t in self.storage.tickets if t.id == ticket_id), None)

    def get_by_ticket_number(self, ticket_number: str) -> Optional[Ticket]:
        return next((t for t in self.storage.tickets if t.ticket_number.upper() == ticket_number.upper()), None)

    def get_all(
        self,
        student_id: Optional[int] = None,
        assigned_staff_id: Optional[int] = None,
        department: Optional[str] = None,
        status: Optional[TicketStatus] = None,
        priority: Optional[Priority] = None,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Ticket]:
        results = self.storage.tickets
        if student_id is not None:
            results = [t for t in results if t.student_id == student_id]
        if assigned_staff_id is not None:
            results = [t for t in results if t.assigned_staff_id == assigned_staff_id]
        if department is not None:
            results = [t for t in results if t.department.lower() == department.lower()]
        if status is not None:
            results = [t for t in results if t.status == status]
        if priority is not None:
            results = [t for t in results if t.priority == priority]
        if category is not None:
            results = [t for t in results if t.category.lower() == category.lower()]
        if search:
            q = search.lower()
            results = [
                t for t in results
                if q in t.ticket_number.lower()
                or q in t.subject.lower()
                or q in t.student_name.lower()
                or (str(t.student_id) == q)
                or q in t.category.lower()
            ]
        # Sort by updated_at descending
        return sorted(results, key=lambda x: x.updated_at, reverse=True)

    def create(self, ticket: Ticket) -> Ticket:
        self.storage.tickets.append(ticket)
        return ticket

    def update(self, ticket: Ticket) -> Ticket:
        ticket.updated_at = datetime.utcnow()
        for idx, t in enumerate(self.storage.tickets):
            if t.id == ticket.id:
                self.storage.tickets[idx] = ticket
                return ticket
        return ticket
