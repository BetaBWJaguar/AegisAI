from dataclasses import dataclass, asdict, field
from datetime import datetime, date
import uuid
from typing import List, Optional

from bson import ObjectId
from pydantic import EmailStr

from user.device import Device
from user.failedloginattempt import FailedLoginAttempt
from user.validationmixin import ValidationMixin
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
    email_verified: bool = False
    email_verification_token: Optional[str] = None
    email_verified_at: Optional[datetime] = None
    devices: List[Device] = field(default_factory=list)
    failed_login_attempts: List[FailedLoginAttempt] = field(default_factory=list)
    _id: str = field(default_factory=lambda: str(ObjectId()))

    @staticmethod
    def create(username: str, email: EmailStr, password: str,
               full_name: str, birth_date: date, phone_number: str,
               status: str = "PENDING_VERIFICATION", role: Role = Role.USER) -> "User":


        ValidationMixin.validate_username(username)
        ValidationMixin.validate_email(email)
        ValidationMixin.validate_password(password)
        ValidationMixin.validate_birth_date(birth_date)

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


    def set_verification_token(self, token: str):
        self.email_verification_token = token
        self.updated_at = datetime.utcnow()

    def mark_email_verified(self):
        self.email_verified = True
        self.email_verified_at = datetime.utcnow()
        self.email_verification_token = None
        self.status = "ACTIVE"
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
        if self.email_verified_at:
            data["email_verified_at"] = self.email_verified_at.isoformat()

        if isinstance(data.get("role"), str):
            data["role"] = Role[data["role"]]
        data["workspaces"] = [ws.to_dict() for ws in self.workspaces]
        data["devices"] = [d.to_dict() for d in self.devices]
        data["failed_login_attempts"] = [f.to_dict() for f in self.failed_login_attempts]

        return data
