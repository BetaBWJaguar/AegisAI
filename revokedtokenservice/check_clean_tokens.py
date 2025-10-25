from datetime import datetime
from revokedtokenservice.revoked_token_service import RevokedTokenService

def main():
    try:
        revoked_service = RevokedTokenService("config.json")

        deleted_count = revoked_service.cleanup_expired()

        if deleted_count > 0:
            print(f"[{datetime.utcnow()}] ✅ {deleted_count} expired token(s) removed from revoked_tokens.")
        else:
            print(f"[{datetime.utcnow()}] ✅ No expired tokens found.")

    except Exception as e:
        print(f"[{datetime.utcnow()}] ❌ Error while cleaning tokens: {e}")
