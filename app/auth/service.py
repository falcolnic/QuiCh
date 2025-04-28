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
    InvalidCredentialsException,
    TokenValidationException,
    UserNotFoundException,
)
from app.models.user import UserModel
from app.schemas.token import TokenSchema
from app.schemas.user import UserLoginSchema, UserRegisterSchema, UserResponseSchema

JWT_SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

log = logging.getLogger(__name__)


def create_user(db: Session, user: UserRegisterSchema) -> UserResponseSchema:
    try:
        query = select(UserModel).where(UserModel.username == user.username)
        if db.scalar(query):
            raise DuplicateUsernameException

        query = select(UserModel).where(UserModel.email == user.email)
        if db.scalar(query):
            raise DuplicateEmailException

        hashed_password = pwd_context.hash(user.password)

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


def authenticate_user(db: Session, email: str, password: str) -> UserModel:
    query = select(UserModel).where(UserModel.email == email)
    user = db.scalar(query)
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise InvalidCredentialsException
    return user


def get_user_profile(db: Session, token: str) -> UserResponseSchema:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise TokenValidationException
    except jwt.JWTError:
        raise TokenValidationException

    query = select(UserModel).where(UserModel.username == username)
    user = db.scalar(query)
    if user is None:
        raise UserNotFoundException

    return UserResponseSchema.model_validate(user)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise TokenValidationException


def login_user_service(
    db: Session, form_data: UserLoginSchema, response: Response
) -> TokenSchema:
    try:
        user = authenticate_user(db, form_data.email, form_data.password)
        access_token = create_access_token(
            data={"uuid": str(user.uuid), "sub": user.username}
        )
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            max_age=3600,  # 1 hour
        )
        return TokenSchema(access_token=access_token)
    except InvalidCredentialsException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


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
