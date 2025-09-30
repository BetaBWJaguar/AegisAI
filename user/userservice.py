from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import date

from pydantic import EmailStr

from user.role import Role
from user.user import User

class UserService(ABC):

    @abstractmethod
    def register_user(self,
                      username: str,
                      email: EmailStr,
                      password: str,
                      full_name: str,
                      birth_date: date,
                      phone_number: str,
                      role: Role = Role.USER) -> User:
        pass

    @abstractmethod
    def get_all_users(self) -> List[User]:
        pass

    @abstractmethod
    def get_user(self, user_id: str) -> Optional[User]:
        pass

    @abstractmethod
    def remove_user(self, user_id: str) -> bool:
        pass

    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[User]:
        pass
