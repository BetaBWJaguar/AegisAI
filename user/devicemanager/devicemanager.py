from datetime import datetime

from user.device import Device

class DeviceManager:

    @staticmethod
    def add_or_update_device(user, device_name: str, ip: str, user_agent: str):
        existing = None

        for d in user.devices:
            if d.device_name == device_name and d.ip_address == ip and d.user_agent == user_agent:
                existing = d
                break

        if existing:
            existing.update_last_active()
            existing.is_active = True
        else:
            new_device = Device.create(device_name, ip, user_agent)
            user.devices.append(new_device)

        user.updated_at = datetime.utcnow()
        return user
