import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.exceptions import InvalidCredentialsException, TokenValidationException
from app.models.user import UserModel

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def authenticate_user(db: Session, email: str, password: str) -> UserModel:
    query = select(UserModel).where(UserModel.email == email)
    user = db.scalar(query)
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise InvalidCredentialsException
    return user


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


def hash_password(password: str) -> str:
    return pwd_context.hash(password)
