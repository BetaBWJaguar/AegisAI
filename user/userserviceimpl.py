from datetime import date, datetime
from typing import List, Optional

from pydantic import EmailStr
from pymongo import MongoClient
from user.user import User
from user.userservice import UserService
from config_loader import ConfigLoader
from user.workspace import Workspace


class UserServiceImpl(UserService):
    def __init__(self, config_path="config.json"):
        config = ConfigLoader(config_path).get_database_config()
        uri = f"mongodb://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['name']}?authSource={config['authSource']}"
        self.client = MongoClient(uri)
        self.db = self.client[config["name"]]
        self.collection = self.db["users"]

    def register_user(self,
                      username: str,
                      email: EmailStr,
                      password: str,
                      full_name: str,
                      birth_date: date,
                      phone_number: str,
                      status: str = "ACTIVE",
                      workspaces: Optional[List[Workspace]] = None) -> User:
        user = User.create(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            birth_date=birth_date,
            phone_number=phone_number,
            status=status
        )


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
        updates["updated_at"] = datetime.now()
        result = self.collection.find_one_and_update(
            {"id": str(user_id)},
            {"$set": updates},
            return_document=True
        )
        return User(**result) if result else None

