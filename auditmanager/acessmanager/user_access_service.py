import uuid
from pymongo import MongoClient
from config_loader import ConfigLoader
from error.errortypes import ErrorType

from error.expectionhandler import ExpectionHandler


class UserAccessService:
    def __init__(self, config_file: str = "config.json"):
        try:
            cfg = ConfigLoader(config_file).get_database_config()
            uri = f"mongodb://{cfg['username']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['authSource']}"
            self.client = MongoClient(uri)
            self.db = self.client[cfg["name"]]
            self.user_collection = self.db["users"]
        except Exception as e:
            raise ExpectionHandler(
                message="Failed to initialize MongoDB connection in UserAccessService.",
                error_type=ErrorType.DATABASE_ERROR,
                detail=str(e)
            )

    def verify_workspace_access(self, user_id: uuid.UUID, workspace_id: uuid.UUID):
        try:
            user = self.user_collection.find_one({"id": str(user_id)})
            if not user:
                raise ExpectionHandler(
                    message="User not found.",
                    error_type=ErrorType.NOT_FOUND,
                    detail=f"User with ID {user_id} not found in database."
                )

            user_workspaces = user.get("workspaces", [])
            owned_workspace_ids = {ws.get("id") for ws in user_workspaces}

            if str(workspace_id) not in owned_workspace_ids:
                raise ExpectionHandler(
                    message="User is not authorized for this workspace.",
                    error_type=ErrorType.PERMISSION_DENIED,
                    detail=f"User {user_id} tried to access workspace {workspace_id}."
                )

        except ExpectionHandler:
            raise
        except Exception as e:
            raise ExpectionHandler(
                message="Failed to verify workspace access.",
                error_type=ErrorType.DATABASE_ERROR,
                detail=str(e)
            )
