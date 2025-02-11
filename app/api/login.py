import logging
import os
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.exceptions import credential_exception
from app.schemas.token import Token
from app.services.security import create_access_token

router = APIRouter()

log = logging.getLogger(__name__)


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    if form_data.password != os.getenv("API_PASSWORD") or form_data.username != os.getenv(
        "API_USER_ID"
    ):
        log.info(f"Invalid login attempt from user: {form_data.username}")

        raise credential_exception

    access_token = create_access_token(subject=os.getenv("API_USER_ID"))
    return Token(access_token=access_token, token_type="bearer")