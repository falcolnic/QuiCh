import logging
from typing import Optional

from click import Option
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.auth.exceptions import (
    DuplicateEmailException,
    DuplicateUsernameException,
    InvalidCredentialsException,
    TokenValidationException,
    UserNotFoundException,
)
from app.auth.service import (
    create_user,
    get_profile_service,
    login_user_service,
    logout_user_service,
)
from app.schemas.token import TokenSchema
from app.schemas.user import UserLoginSchema, UserRegisterSchema, UserResponseSchema

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

log = logging.getLogger(__name__)


@router.post("/register", response_model=UserResponseSchema)
async def register(user: UserRegisterSchema, db: Session = Depends(get_db)):
    try:
        return create_user(db, user)
    except (DuplicateUsernameException, DuplicateEmailException) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        log.error(f"Unexpected error during registration: {e}")
        raise HTTPException(
            status_code=500,
            detail="There was an error, try again later, our admins are already working on it.",
        )


@router.post("/login", response_model=TokenSchema)
async def login(
    form_data: UserLoginSchema, response: Response, db: Session = Depends(get_db)
):
    try:
        return login_user_service(db, form_data, response)
    except InvalidCredentialsException as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        log.error(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=500,
            detail="There was an error, try again later, our admins are already working on it.",
        )


@router.post("/logout")
async def logout(response: Response):
    return logout_user_service(response)


@router.get("/profile")
async def get_profile(
    db: Session = Depends(get_db), access_token: Optional[str] = Cookie(None)
):
    try:
        return get_profile_service(db, access_token)
    except (TokenValidationException, UserNotFoundException) as e:
        raise HTTPException(status_code=401, detail=str(e))
