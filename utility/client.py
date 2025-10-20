from contextvars import ContextVar

class ClientIPStorage:
    _ip: ContextVar[str] = ContextVar("client_ip", default="0.0.0.0")

    @staticmethod
    def set(ip: str):
        ClientIPStorage._ip.set(ip)

    @staticmethod
    def get() -> str:
        return ClientIPStorage._ip.get()
