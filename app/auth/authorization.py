import logging
import os
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.exceptions import credential_exception
from app.jinja_setup import jinja
from app.models.user import UserModel
from app.schemas.token import Token
from app.schemas.user import UserCreateSchema, UserLoginSchema
from app.services.security import create_access_token, get_password_hash

router = APIRouter()

log = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/signup", response_model=UserCreateSchema)
def create_user(user: UserCreateSchema, db: Annotated[Session, Depends(get_db)]):
    hashed_password = get_password_hash(user.password)

    db_user = UserModel(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    access_token = create_access_token(subject=user.username)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    if form_data.password != os.getenv(
        "API_PASSWORD"
    ) or form_data.username != os.getenv("API_USER_ID"):
        log.info(f"Invalid login attempt from user: {form_data.username}")

        raise credential_exception

    access_token = create_access_token(subject=os.getenv("API_USER_ID"))
    return Token(access_token=access_token, token_type="bearer")


@router.get("/signup")
@jinja.page("signup.jinja2")
def signup_page() -> None:
    """This route serves the signup.jinja2 template."""
    return {}


@router.get("/login")
@jinja.page("login.jinja2")
def login_page(login_data: UserLoginSchema) -> None:
    """This route serves the login.jinja2 template."""
    # TODO: Add logic to handle login using login_data.username and login_data.password
    return {}
