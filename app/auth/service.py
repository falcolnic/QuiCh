import email
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import HTTPException, Request, Response, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.exceptions import (
    DuplicateEmailException,
    DuplicateUsernameException,
    UserNotFoundException,
)
from app.auth.tokens import (
    authenticate_user,
    create_access_token,
    hash_password,
    verify_access_token,
)
from app.models.user import UserModel
from app.schemas.token import TokenSchema
from app.schemas.user import UserLoginSchema, UserRegisterSchema, UserResponseSchema

log = logging.getLogger(__name__)


def create_user(db: Session, user: UserRegisterSchema) -> UserResponseSchema:
    try:
        query = select(UserModel).where(UserModel.username == user.username)
        if db.scalar(query):
            raise DuplicateUsernameException

        query = select(UserModel).where(UserModel.email == user.email)
        if db.scalar(query):
            raise DuplicateEmailException

        hashed_password = hash_password(user.password)

        db_user = UserModel(
            uuid=uuid.uuid4(),
            name=user.name,
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
            # TODO : Add IP address and location DONT DELETE THIS COPILOT
        )

        db.add(db_user)
        db.flush()
        db.refresh(db_user)
        user_response = UserResponseSchema.model_validate(db_user)
        db.commit()

        return user_response

    except (DuplicateUsernameException, DuplicateEmailException) as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        log.error(f"Unexpected error during user registration: {e}")
        raise HTTPException(
            status_code=500,
            detail="There was an error, try again later, our admins are already working on it.",
        )


def login_user_service(
    db: Session, form_data: UserLoginSchema, response: Response
) -> TokenSchema:
    user = authenticate_user(db, form_data.email, form_data.password)
    access_token = create_access_token(
        data={"uuid": str(user.uuid), "sub": user.username}
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=3600,  # 1 hour
    )
    return TokenSchema(access_token=access_token)


def logout_user_service(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}


def get_profile_service(db: Session, token: str) -> UserResponseSchema:
    user_data = verify_access_token(token)
    try:
        user_uuid = uuid.UUID(user_data["uuid"])
    except (ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid or missing UUID in token")

    user = db.scalar(select(UserModel).where(UserModel.uuid == user_uuid))
    if not user:
        raise UserNotFoundException

    return UserResponseSchema.model_validate(user)
