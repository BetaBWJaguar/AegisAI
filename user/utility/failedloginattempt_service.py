from datetime import datetime, timedelta
from user.userserviceimpl import UserServiceImpl

class FailedLoginAttemptService:
    service = UserServiceImpl()

    @staticmethod
    def remove_expired_attempts_for_all_users(expiry_hours=6):
        users = FailedLoginAttemptService.service.collection.find({})
        threshold_time = datetime.utcnow() - timedelta(hours=expiry_hours)

        for doc in users:
            user_id = doc.get("id")
            attempts = doc.get("failed_login_attempts", [])
            if not attempts:
                continue

            filtered = []
            for f in attempts:
                ts = f["timestamp"]
                ts = datetime.fromisoformat(ts) if isinstance(ts, str) else ts
                if ts >= threshold_time:
                    filtered.append(f)

            if len(filtered) != len(attempts):
                FailedLoginAttemptService.service.update_user(
                    user_id=str(user_id),
                    updates={
                        "failed_login_attempts": filtered,
                        "updated_at": datetime.utcnow()
                    }
                )
