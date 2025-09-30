from dataclasses import dataclass, asdict, field
from datetime import datetime, date
import uuid
from typing import List, Optional
from pydantic import EmailStr

from user.workspace import Workspace
from user.role import Role

@dataclass
class User:
    id: uuid.UUID
    username: str
    email: EmailStr
    password: str
    full_name: str
    birth_date: date
    phone_number: str
    created_at: datetime
    updated_at: datetime
    status: str
    role: Role = Role.USER
    workspaces: List[Workspace] = field(default_factory=list)
    _id: Optional[str] = None

    @staticmethod
    def create(username: str, email: EmailStr, password: str,
               full_name: str, birth_date: date, phone_number: str,
               status: str = "ACTIVE", role: Role = Role.USER) -> "User":
        now = datetime.utcnow()
        return User(
            id=uuid.uuid4(),
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            birth_date=birth_date,
            phone_number=phone_number,
            created_at=now,
            updated_at=now,
            status=status,
            role=role,
            workspaces=[]
        )

    def add_workspace(self, workspace: Workspace):
        self.workspaces.append(workspace)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["id"] = str(self.id)

        if isinstance(self.birth_date, date):
            data["birth_date"] = self.birth_date.isoformat()
        if isinstance(self.created_at, datetime):
            data["created_at"] = self.created_at.isoformat()
        if isinstance(self.updated_at, datetime):
            data["updated_at"] = self.updated_at.isoformat()

        data["role"] = self.role.value

        data["workspaces"] = [ws.to_dict() for ws in self.workspaces]
        return data
