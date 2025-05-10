import json
import logging
import uuid
from typing import Optional

import httpx
from fastapi import APIRouter, Cookie, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.auth.tokens import verify_access_token
from app.models.user import UserModel

router = APIRouter()
log = logging.getLogger(__name__)


async def proxy_ipinfo(request: Request):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://ipapi.co/json/")

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "unknown time")
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded with external API",
                        "retry_after": retry_after,
                        "message": "The service is currently rate limited. Please try again later.",
                    },
                    headers=(
                        {"Retry-After": retry_after}
                        if "Retry-After" in response.headers
                        else {}
                    ),
                )

            response.raise_for_status()
            if not response.content:
                return JSONResponse(
                    status_code=502,
                    content={"error": "Empty response from external API"},
                )
            try:
                data = response.json()
                return JSONResponse(content=data)
            except json.JSONDecodeError:
                return JSONResponse(
                    status_code=502,
                    content={
                        "error": "Invalid JSON response from external API",
                        "content": response.text[:100],
                    },
                )

    except httpx.HTTPError as e:
        return JSONResponse(
            status_code=502,
            content={"error": f"Error communicating with external API: {str(e)}"},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"Internal server error: {str(e)}"}
        )


@router.get("/proxy/location")
async def get_user_location(
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
):
    try:
        if access_token:
            user_data = verify_access_token(access_token)
            try:
                user_uuid = uuid.UUID(user_data["uuid"])
                user = db.scalar(select(UserModel).where(UserModel.uuid == user_uuid))
                if user and (user.ip_address or user.location):
                    return {
                        "ip": user.ip_address,
                        "city": user.location.split(", ")[0] if user.location else None,
                        "region": (
                            user.location.split(", ")[1]
                            if user.location and len(user.location.split(", ")) > 1
                            else None
                        ),
                        "country_name": (
                            user.location.split(", ")[-1] if user.location else None
                        ),
                    }
            except (ValueError, KeyError, Exception) as e:
                log.error(f"Error retrieving user data: {e}")

    except Exception as e:
        log.error(f"Error processing token: {e}")

    return await proxy_ipinfo(request)


@router.get("/proxy/ipinfo")
async def proxy_ipinfo_endpoint(request: Request):
    return await proxy_ipinfo(request)
