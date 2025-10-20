from starlette.middleware.base import BaseHTTPMiddleware

from utility.client import ClientIPStorage


class ClientIPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        ip = request.headers.get("x-forwarded-for", request.client.host)
        if ip and "," in ip:
            ip = ip.split(",")[0].strip()

        ClientIPStorage.set(ip)
        response = await call_next(request)
        return response
