from fastapi import Depends, HTTPException, status
from auth.authcontroller import get_current_user
from user.role import Role


def require_perm(allowed_roles: list[Role]):

    def wrapper(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        return current_user

    return wrapper
