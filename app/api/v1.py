from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from app.api.deps import get_current_user
from app.api.routers import router as general_routers
from app.api.transcript import router as transcript_router
from app.auth.routers import router as auth_routers

PROTECTED = Depends(get_current_user)

# WARNING: Don't use this unless you want unauthenticated routes
unauthenticated_api_router = APIRouter()
unauthenticated_api_router.include_router(
    auth_routers, tags=["Authorization"], prefix="/v1"
)
unauthenticated_api_router.include_router(general_routers, tags=["Routers"])

# NOTE: All api routes should be authenticated by default
authenticated_api_router = APIRouter()
authenticated_api_router.include_router(transcript_router, tags=["Transcripts"])


api_router = APIRouter(default_response_class=JSONResponse)
api_router.include_router(unauthenticated_api_router)
api_router.include_router(
    authenticated_api_router, dependencies=[PROTECTED], prefix="/api"
)
