from typing import List
from app.models.schemas import (
    User, Ticket, Activity, Notification, Escalation, SLAPolicy
)

class InMemoryStorage:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InMemoryStorage, cls).__new__(cls)
            cls._instance._init_storage()
        return cls._instance

    def _init_storage(self):
        self.users: List[User] = []
        self.tickets: List[Ticket] = []
        self.activities: List[Activity] = []
        self.notifications: List[Notification] = []
        self.escalations: List[Escalation] = []
        self.sla_policies: List[SLAPolicy] = []
        self.departments: List[str] = [
            "Finance",
            "Academic Affairs",
            "Registrar & Student Records",
            "Campus Administration",
            "Student Support Services"
        ]

        # Auto-increment counters
        self._user_counter: int = 1
        self._ticket_counter: int = 100
        self._activity_counter: int = 1
        self._notification_counter: int = 1
        self._escalation_counter: int = 1

    def next_user_id(self) -> int:
        curr = self._user_counter
        self._user_counter += 1
        return curr

    def next_ticket_id(self) -> int:
        curr = self._ticket_counter
        self._ticket_counter += 1
        return curr

    def next_activity_id(self) -> int:
        curr = self._activity_counter
        self._activity_counter += 1
        return curr

    def next_notification_id(self) -> int:
        curr = self._notification_counter
        self._notification_counter += 1
        return curr

    def next_escalation_id(self) -> int:
        curr = self._escalation_counter
        self._escalation_counter += 1
        return curr

    def reset(self):
        """Used in test suites to clear state"""
        self._init_storage()

db = InMemoryStorage()
