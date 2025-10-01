from fastapi import APIRouter, HTTPException, Depends
from typing import List

from auth.authcontroller import get_current_user
from user.create.create import UserCreate
from user.response.response import UserResponse
from user.role import Role
from user.upsert.upsert import UserUpdate
from user.userserviceimpl import UserServiceImpl

router = APIRouter()
service = UserServiceImpl("config.json")

def require_admin(current_user):
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Only admins can perform this action"
        )
    return current_user


@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, current_user=Depends(get_current_user)):

    await require_admin(current_user)

    new_user = service.register_user(
        username=user.username,
        email=user.email,
        password=user.password,
        full_name=user.full_name,
        birth_date=user.birth_date,
        phone_number=user.phone_number,
    )
    return new_user.to_dict()


@router.get("/", response_model=List[UserResponse])
async def list_users(current_user=Depends(get_current_user)):
    users = service.get_all_users()
    return [u.to_dict() for u in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user=Depends(get_current_user)):
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict()


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, payload: UserUpdate, current_user=Depends(get_current_user)):

    await require_admin(current_user)
    updates = payload.dict(exclude_unset=True)

    if "email" in updates:
        existing = service.get_user_by_email(str(updates["email"]))
        if existing and str(existing.id) != user_id:
            raise HTTPException(status_code=400, detail="Email already in use")

    if "birth_date" in updates and updates["birth_date"] is not None:
        updates["birth_date"] = updates["birth_date"].isoformat()

    updated = service.update_user(user_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated.to_dict()


@router.delete("/{user_id}")
async def delete_user(user_id: str, current_user=Depends(get_current_user)):

    await require_admin(current_user)
    success = service.remove_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"deleted": True}
