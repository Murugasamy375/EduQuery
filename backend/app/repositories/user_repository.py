from typing import List, Optional
from app.models.schemas import User
from app.models.enums import UserRole
from app.storage.memory import db

class UserRepository:
    def __init__(self, storage=db):
        self.storage = storage

    def get_by_id(self, user_id: int) -> Optional[User]:
        return next((u for u in self.storage.users if u.id == user_id), None)

    def get_by_email(self, email: str) -> Optional[User]:
        return next((u for u in self.storage.users if u.email.lower() == email.lower()), None)

    def get_all(self, role: Optional[UserRole] = None, department: Optional[str] = None) -> List[User]:
        users = self.storage.users
        if role:
            users = [u for u in users if u.role == role]
        if department:
            users = [u for u in users if u.department == department]
        return users

    def create(self, user: User) -> User:
        self.storage.users.append(user)
        return user

    def update(self, user: User) -> User:
        for idx, u in enumerate(self.storage.users):
            if u.id == user.id:
                self.storage.users[idx] = user
                return user
        return user
