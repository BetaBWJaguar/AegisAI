from datetime import datetime
from user.device import Device
from user_agents import parse

class DeviceManager:

    @staticmethod
    def extract_device_name(user_agent: str) -> str:
        ua = parse(user_agent)

        device = ua.device.family or "Unknown Device"
        os = ua.os.family + (" " + ua.os.version_string if ua.os.version_string else "")
        browser = ua.browser.family

        return f"{device} / {os} / {browser}"

    @staticmethod
    def add_or_update_device(user_id: str, service, device_name: str, ip: str, user_agent: str, is_login: bool):
        user = service.get_user(user_id)
        if not user:
            return None

        existing = next((d for d in (user.devices or []) if d.device_name == device_name), None)
        now = datetime.utcnow()

        if existing:
            updated_devices = []
            for dev in user.devices:
                if dev.device_name == device_name:
                    dev.ip_address = ip
                    dev.user_agent = user_agent
                    dev.last_active = now
                    if is_login:
                        dev.login_time = now
                        dev.is_active = True
                        dev.logout_time = None

                updated_devices.append(dev.to_dict())

            return service.update_user(user_id, {
                "devices": updated_devices,
                "updated_at": now
            })

        else:
            new_device = Device.create(
                device_name=device_name,
                ip_address=ip,
                user_agent=user_agent,
                is_active=is_login
            )

            if is_login:
                new_device.login_time = now
                new_device.last_active = now

            updated_devices = [dev.to_dict() for dev in (user.devices or [])]
            updated_devices.append(new_device.to_dict())

            return service.update_user(user_id, {
                "devices": updated_devices,
                "updated_at": now
            })
