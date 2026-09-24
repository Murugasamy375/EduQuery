from typing import List, Optional
from app.models.schemas import Activity, Notification, Escalation
from app.storage.memory import db

class ActivityRepository:
    def __init__(self, storage=db):
        self.storage = storage

    def get_by_ticket_id(self, ticket_id: int, include_internal: bool = True) -> List[Activity]:
        activities = [a for a in self.storage.activities if a.ticket_id == ticket_id]
        if not include_internal:
            activities = [a for a in activities if not a.is_internal]
        return sorted(activities, key=lambda x: x.created_at)

    def create(self, activity: Activity) -> Activity:
        self.storage.activities.append(activity)
        return activity


class NotificationRepository:
    def __init__(self, storage=db):
        self.storage = storage

    def get_by_user_id(self, user_id: int, limit: int = 50) -> List[Notification]:
        notifs = [n for n in self.storage.notifications if n.user_id == user_id]
        notifs = sorted(notifs, key=lambda x: x.created_at, reverse=True)
        return notifs[:limit]

    def create(self, notification: Notification) -> Notification:
        self.storage.notifications.append(notification)
        return notification

    def mark_as_read(self, notification_id: int, user_id: int) -> Optional[Notification]:
        for n in self.storage.notifications:
            if n.id == notification_id and n.user_id == user_id:
                n.is_read = True
                return n
        return None

    def mark_all_read(self, user_id: int):
        for n in self.storage.notifications:
            if n.user_id == user_id:
                n.is_read = True


class EscalationRepository:
    def __init__(self, storage=db):
        self.storage = storage

    def get_by_ticket_id(self, ticket_id: int) -> List[Escalation]:
        return [e for e in self.storage.escalations if e.ticket_id == ticket_id]

    def create(self, escalation: Escalation) -> Escalation:
        self.storage.escalations.append(escalation)
        return escalation
