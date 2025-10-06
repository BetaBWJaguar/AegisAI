from fastapi import APIRouter, Depends
from typing import List

from auth.authcontroller import get_current_user
from error.expectionhandler import ExpectionHandler
from permcontrol.permissionscontrol import require_perm
from user.create.create import UserCreate
from user.response.response import UserResponse
from user.role import Role
from user.upsert.upsert import UserUpdate
from user.userserviceimpl import UserServiceImpl

from error.errortypes import ErrorType

router = APIRouter()
service = UserServiceImpl("config.json")


@router.post(
    "/",
    response_model=UserResponse,
    dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))]
)
async def create_user(user: UserCreate, current_user=Depends(get_current_user)):
    try:
        new_user = service.register_user(
            username=user.username,
            email=user.email,
            password=user.password,
            full_name=user.full_name,
            birth_date=user.birth_date,
            phone_number=user.phone_number,
        )
        return new_user.to_dict()

    except ValueError as e:
        raise ExpectionHandler(
            message="Invalid user data provided.",
            error_type=ErrorType.VALIDATION_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise ExpectionHandler(
            message="An unexpected error occurred while creating user.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.get(
    "/",
    response_model=List[UserResponse]
)
async def list_users(current_user=Depends(get_current_user)):
    try:
        users = service.get_all_users()
        return [u.to_dict() for u in users]
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to list users.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse
)
async def get_user(user_id: str, current_user=Depends(get_current_user)):
    try:
        user = service.get_user(user_id)
        if not user:
            raise ExpectionHandler(
                message=f"User with ID '{user_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )
        return user.to_dict()
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Error occurred while fetching user.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))]
)
async def update_user(user_id: str, payload: UserUpdate, current_user=Depends(get_current_user)):
    try:
        updates = payload.dict(exclude_unset=True)

        if "email" in updates:
            existing = service.get_user_by_email(str(updates["email"]))
            if existing and str(existing.id) != user_id:
                raise ExpectionHandler(
                    message="Email already in use by another user.",
                    error_type=ErrorType.VALIDATION_ERROR
                )

        if "birth_date" in updates and updates["birth_date"] is not None:
            updates["birth_date"] = updates["birth_date"].isoformat()

        updated = service.update_user(user_id, updates)
        if not updated:
            raise ExpectionHandler(
                message=f"User with ID '{user_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )
        return updated.to_dict()

    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Error occurred while updating user.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )


@router.delete(
    "/{user_id}",
    dependencies=[Depends(require_perm([Role.ADMIN, Role.DEVELOPER]))]
)
async def delete_user(user_id: str, current_user=Depends(get_current_user)):
    try:
        success = service.remove_user(user_id)
        if not success:
            raise ExpectionHandler(
                message=f"User with ID '{user_id}' not found.",
                error_type=ErrorType.NOT_FOUND
            )
        return {"deleted": True, "message": "User deleted successfully."}
    except ExpectionHandler:
        raise
    except Exception as e:
        raise ExpectionHandler(
            message="Failed to delete user.",
            error_type=ErrorType.DATABASE_ERROR,
            detail=str(e)
        )
