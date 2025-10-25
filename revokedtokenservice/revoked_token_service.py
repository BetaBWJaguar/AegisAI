from datetime import datetime
from pymongo import MongoClient
from config_loader import ConfigLoader


class RevokedTokenService:
    def __init__(self, config_file: str = "config.json"):
        cfg = ConfigLoader(config_file).get_database_config()
        uri = f"mongodb://{cfg['username']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['authSource']}"

        self.client = MongoClient(uri)
        self.db = self.client[cfg["name"]]
        self.collection = self.db["revoked_tokens"]

    def revoke_token(self, jti: str, user_id: str, expires_at: datetime) -> bool:
        if not jti or not user_id:
            return False

        already_revoked = self.collection.find_one({"jti": jti})
        if already_revoked:
            return False

        self.collection.insert_one({
            "jti": jti,
            "user_id": user_id,
            "revoked_at": datetime.utcnow(),
            "expires_at": expires_at
        })
        return True

    def is_token_revoked(self, jti: str) -> bool:
        if not jti:
            return False
        return self.collection.find_one({"jti": jti}) is not None

    def cleanup_expired(self) -> int:
        now = datetime.utcnow()
        result = self.collection.delete_many({"expires_at": {"$lte": now}})
        return result.deleted_count
