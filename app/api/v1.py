from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from app.api import transcript
from app.api.deps import get_current_user
from app.config import app_config
from app.auth import authorization

PROTECTED = Depends(get_current_user)

# WARNING: Don't use this unless you want unauthenticated routes
unauthenticated_api_router = APIRouter()
unauthenticated_api_router.include_router(authorization.router, tags=["Authorization"], prefix="/v1")

# NOTE: All api routes should be authenticated by default
authenticated_api_router = APIRouter()
authenticated_api_router.include_router(transcript.router, tags=["Transcripts"])
api_router = APIRouter(default_response_class=JSONResponse)

api_router.include_router(unauthenticated_api_router)
api_router.include_router(authenticated_api_router, dependencies=[PROTECTED], prefix="/api")