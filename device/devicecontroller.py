from fastapi import APIRouter, Depends
from datetime import datetime

from auth.authcontroller import decode_token
from user.userserviceimpl import UserServiceImpl
from revokedtokenservice.revoked_token_service import RevokedTokenService
from error.expectionhandler import ExpectionHandler
from error.errortypes import ErrorType
from user.devicemanager.devicemanager import DeviceManager

router = APIRouter()
service = UserServiceImpl()
revoked_service = RevokedTokenService()


@router.get("/active")
async def get_active_devices(current_user=Depends(decode_token)):
    user = service.get_user(current_user.user_id)

    if not user:
        raise ExpectionHandler(
            message="User not found.",
            error_type=ErrorType.NOT_FOUND
        )

    if not user.devices:
        return {"success": True, "devices": []}

    active_devices = [dev.to_dict() for dev in user.devices if dev.is_active]

    return {
        "success": True,
        "count": len(active_devices),
        "devices": active_devices
    }


@router.delete("/logout/{device_name}")
async def logout_specific_device(device_name: str, current_user=Depends(decode_token)):
    user = service.get_user(current_user.user_id)

    if not user:
        raise ExpectionHandler(
            message="User not found.",
            error_type=ErrorType.NOT_FOUND
        )

    if not user.devices:
        raise ExpectionHandler(
            message="User has no registered devices.",
            error_type=ErrorType.NOT_FOUND
        )

    target = next((d for d in user.devices if d.device_name == device_name and d.is_active), None)
    if not target:
        raise ExpectionHandler(
            message=f"Device '{device_name}' not found or already inactive.",
            error_type=ErrorType.NOT_FOUND
        )

    DeviceManager.set_inactive_single(
        user_id=str(user.id),
        service=service,
        device_name=device_name
    )

    return {
        "success": True,
        "message": f"Successfully logged out from device '{device_name}'."
    }
