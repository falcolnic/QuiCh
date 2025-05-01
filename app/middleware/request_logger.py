import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

log = logging.getLogger(__name__)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        user_uuid = request.cookies.get("access_token")
        if user_uuid:
            log.info(f"Request made by user UUID: {user_uuid}")
        response = await call_next(request)
        return response
