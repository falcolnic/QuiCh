from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from app.api.deps import get_current_user
from app.api.routers import router as general_routers
from app.api.transcript import router as transcript_router
from app.auth.locations import router as locations_router
from app.auth.routers import router as auth_routers

PROTECTED = Depends(get_current_user)

# Create a single unauthenticated router
unauthenticated_api_router = APIRouter()
unauthenticated_api_router.include_router(
    auth_routers, tags=["Authorization"], prefix="/v1"
)
unauthenticated_api_router.include_router(general_routers, tags=["Routers"])

# Create a dedicated location router for public endpoints
# Include only the location endpoints that should be accessible without authentication
location_public_router = APIRouter(prefix="/v1")
location_public_router.include_router(locations_router, tags=["Locations"])

# Create authenticated router for protected endpoints
authenticated_api_router = APIRouter()
authenticated_api_router.include_router(transcript_router, tags=["Transcripts"])
# We'll skip adding locations_router here since we're using the same endpoints for both authenticated and unauthenticated access

# Combine all routers
api_router = APIRouter(default_response_class=JSONResponse)
api_router.include_router(unauthenticated_api_router)
api_router.include_router(location_public_router)
api_router.include_router(
    authenticated_api_router, dependencies=[PROTECTED], prefix="/api"
)
