"""Flask-Login compatible user object backed by public.users/auth.users."""
from dataclasses import dataclass
from typing import Optional

from flask_login import UserMixin


@dataclass
class SupabaseUser(UserMixin):
    id: str
    auth_user_id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    role: str
    is_active: bool
    raw: dict

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def role_name(self) -> str:
        return self.role

    def get_id(self) -> str:
        return self.id

    def has_role(self, *role_names: str) -> bool:
        return self.role in role_names
