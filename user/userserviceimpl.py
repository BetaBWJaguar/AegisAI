import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import EmailStr
from pymongo import MongoClient

from user.device import Device
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

    def get_user(self, user_id: str):
        doc = self.collection.find_one({"id": str(user_id)})
        if not doc:
            return None

        from user.workspace import Workspace
        from user.rule import Rule
        from user.violations import Violation
        from user.device import Device

        if "workspaces" in doc and doc["workspaces"]:
            doc["workspaces"] = [
                Workspace(
                    id=uuid.UUID(ws["id"]),
                    name=ws["name"],
                    description=ws.get("description", ""),
                    rules=[Rule(**r) if isinstance(r, dict) else r for r in ws.get("rules", [])],
                    violations=[Violation(**v) if isinstance(v, dict) else v for v in ws.get("violations", [])],
                    language=ws.get("language", "tr"),
                    created_at=datetime.fromisoformat(ws["created_at"]) if "created_at" in ws else datetime.utcnow(),
                    updated_at=datetime.fromisoformat(ws["updated_at"]) if "updated_at" in ws else datetime.utcnow(),
                )
                for ws in doc.get("workspaces", [])
            ]
        else:
            doc["workspaces"] = []


        if "devices" in doc and doc["devices"]:
            doc["devices"] = [
                Device(
                    id=uuid.UUID(d["id"]),
                    device_name=d["device_name"],
                    ip_address=d["ip_address"],
                    user_agent=d["user_agent"],
                    login_time=datetime.fromisoformat(d["login_time"]) if isinstance(d["login_time"], str) else d["login_time"],
                    last_active=datetime.fromisoformat(d["last_active"]) if isinstance(d["last_active"], str) else d["last_active"],
                    is_active=d.get("is_active", True),
                    logout_time=((datetime.fromisoformat(d["logout_time"]) if isinstance(d["logout_time"], str) else d["logout_time"]) if d.get("logout_time") else None)
                )
                for d in doc.get("devices", [])
            ]
        else:
            doc["devices"] = []


        return User(**doc)


    def get_user_by_email(self, email: EmailStr) -> Optional[User]:
        user_data = self.collection.find_one({"email": str(email)})

        if not user_data:
            return None
        devices_data = user_data.get("devices", [])
        if devices_data:
            user_data["devices"] = [Device(**d) for d in devices_data]
        else:
            user_data["devices"] = []
        return User(**user_data)

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

        if "devices" in updates:
            existing_devices = user.devices or []
            new_devices = updates["devices"]

            merged_devices = []

            for new_dev in new_devices:
                new_dev_name = new_dev["device_name"] if isinstance(new_dev, dict) else new_dev.device_name
                new_dev_dict = new_dev if isinstance(new_dev, dict) else new_dev.to_dict()

                found = False
                for old_dev in existing_devices:
                    if old_dev.device_name == new_dev_name:
                        old_dev.login_time = datetime.utcnow()
                        old_dev.is_active = True
                        old_dev.logout_time = None
                        old_dev.last_active = None

                        merged_devices.append(old_dev.to_dict())
                        found = True
                        break

                if not found:
                    merged_devices.append(new_dev_dict)

            for old_dev in existing_devices:
                if not any(d["device_name"] == old_dev.device_name for d in merged_devices):
                    merged_devices.append(old_dev.to_dict())

            updates["devices"] = merged_devices

        updates["updated_at"] = datetime.utcnow()

        result = self.collection.find_one_and_update(
            {"id": str(user_id)},
            {"$set": updates},
            return_document=True
        )

        return User(**result) if result else None


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

