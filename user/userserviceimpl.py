from datetime import date, datetime
from typing import List, Optional

from pydantic import EmailStr
from pymongo import MongoClient
from user.user import User
from user.userservice import UserService
from config_loader import ConfigLoader
from user.workspace import Workspace
from utility.emailverificationutility import EmailVerificationUtility


class UserServiceImpl(UserService):
    def __init__(self, config_path="config.json"):
        config = ConfigLoader(config_path).get_database_config()
        uri = f"mongodb://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['name']}?authSource={config['authSource']}"
        self.client = MongoClient(uri)
        self.db = self.client[config["name"]]
        self.collection = self.db["users"]

    def register_user(
            self,
            username: str,
            email: EmailStr,
            password: str,
            full_name: str,
            birth_date: date,
            phone_number: str,
            workspaces: Optional[List[Workspace]] = None,
            email_verified: bool = False,
            verification_token: Optional[str] = None
    ) -> User:
        user = User.create(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            birth_date=birth_date,
            phone_number=phone_number,
        )

        user.email_verified = email_verified
        if verification_token:
            user.set_verification_token(verification_token)

        if workspaces:
            for ws in workspaces:
                user.add_workspace(ws)

        self.collection.insert_one(user.to_dict())
        return user


    def get_all_users(self) -> List[User]:
        docs = self.collection.find()
        return [User(**doc) for doc in docs]

    def get_user(self, user_id: str) -> Optional[User]:
        doc = self.collection.find_one({"id": user_id})
        return User(**doc) if doc else None

    def get_user_by_email(self, email: EmailStr) -> Optional[User]:
        doc = self.collection.find_one({"email": email})
        return User(**doc) if doc else None

    def remove_user(self, user_id: str) -> bool:
        result = self.collection.delete_one({"id": user_id})
        return result.deleted_count > 0

    def update_user(self, user_id: str, updates: dict) -> Optional[User]:
        user = self.get_user(user_id)
        if not user:
            return None

        if "email" in updates and updates["email"] != str(user.email):
            updates["email_verified"] = False
            updates["email_verification_token"] = None
            updates["email_verified_at"] = None
            updates["status"] = "PENDING_VERIFICATION"

            email_utility = EmailVerificationUtility(self)
            token = email_utility.create_verification_token(user_id)
            email_utility.send_verification_email(
                to_email=updates["email"],
                username=user.username,
                user_id=user_id
            )

            updates["email_verification_token"] = token

        updates["updated_at"] = datetime.utcnow()

        result = self.collection.find_one_and_update(
            {"id": str(user_id)},
            {"$set": updates},
            return_document=True
        )

        if not result:
            return None

        updated_user = User(**result)


        return updated_user

    def set_verification_token(self, user_id: str, token: str) -> Optional[User]:
        user = self.get_user(user_id)
        if not user:
            return None
        user.set_verification_token(token)
        self.collection.update_one(
            {"id": str(user_id)},
            {"$set": {
                "email_verification_token": token,
                "updated_at": datetime.utcnow()
            }}
        )
        return user

    def mark_email_verified(self, user_id: str) -> Optional[User]:
        user = self.get_user(user_id)
        if not user:
            return None

        user.mark_email_verified()
        self.collection.update_one(
            {"id": str(user_id)},
            {"$set": {
                "email_verified": True,
                "email_verification_token": None,
                "email_verified_at": datetime.utcnow(),
                "status": "ACTIVE",
                "updated_at": datetime.utcnow()
            }}
        )
        return user

