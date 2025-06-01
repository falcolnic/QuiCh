import logging
from typing import Optional

from fastapi import APIRouter, Body, Cookie, Depends, Form, HTTPException, Response
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.auth.exceptions import (
    CookieNotFoundException,
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
from app.jinja_setup import jinja
from app.schemas.token import TokenSchema
from app.schemas.user import UserLoginSchema, UserRegisterSchema, UserResponseSchema

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

log = logging.getLogger(__name__)


@router.get("/signup")
@jinja.page("signup.jinja2")
async def signup_page():
    return {}


@router.post("/signup", response_model=UserResponseSchema)
async def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    ip_address: str = Form(None),
    location: str = Form(None),
    db: Session = Depends(get_db),
):
    try:
        user = UserRegisterSchema(
            username=username,
            email=email,
            password=password,
            ip_address=ip_address,
            location=location,
        )
        return create_user(db, user)
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            field = error["loc"][0]
            message = error["msg"]
            error_messages.append(f"{field}: {message}")

        raise HTTPException(status_code=422, detail="; ".join(error_messages))
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


@router.get("/signin")
@jinja.page("signin.jinja2")
async def signin_page():
    return {}


@router.post("/signin", response_model=TokenSchema)
async def login(
    user_data: UserLoginSchema, response: Response, db: Session = Depends(get_db)
):
    try:
        if " " in user_data.password:
            raise HTTPException(
                status_code=400, detail="Password cannot contain spaces"
            )

        return login_user_service(db, user_data, response)
    except InvalidCredentialsException as e:
        raise HTTPException(
            status_code=401, detail=str(e), headers={"WWW-Authenticate": "Bearer"}
        )
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
    except (
        TokenValidationException,
        UserNotFoundException,
        CookieNotFoundException,
    ) as e:
        raise HTTPException(status_code=401, detail=str(e))
