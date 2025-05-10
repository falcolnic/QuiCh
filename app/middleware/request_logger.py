import logging

import jwt
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

log = logging.getLogger(__name__)


class RequestLoggerMiddleware(CORSMiddleware):
    async def dispatch(self, request: Request, call_next):
        access_token = request.cookies.get("access_token")
        user_uuid = None

        if access_token:
            try:
                from app.auth.tokens import verify_access_token

                try:
                    user_data = verify_access_token(access_token)
                    user_uuid = user_data.get("uuid")
                    if user_uuid:
                        log.info(f"Request made by user UUID: {user_uuid}")
                except jwt.ExpiredSignatureError:
                    log.info("Request with expired JWT token")
                except jwt.InvalidTokenError:
                    log.info("Request with invalid JWT token")
            except Exception as e:
                log.error(f"Error processing token: {e}")

        response = await call_next(request)
        if user_uuid:
            response.headers["X-User-UUID"] = user_uuid
        else:
            response.headers["X-User-UUID"] = "unknown"
        return response
