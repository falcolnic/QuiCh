from datetime import datetime, timedelta
from typing import Any, Union

import jwt
from jwt import PyJWTError
from passlib.context import CryptContext

from app.config import app_config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(subject: Union[str, Any]) -> str:
    expire = datetime.utcnow() + timedelta(
        minutes=app_config.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.utcnow(),
    }
    encoded_jwt = jwt.encode(
        to_encode,
        app_config.SECRET_KEY,
        algorithm=app_config.ALGORITHM,
    )

    return encoded_jwt


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def decode_access_token(token: str) -> Union[str, Any]:
    try:
        payload = jwt.decode(
            token,
            app_config.SECRET_KEY,
            algorithms=[app_config.ALGORITHM],
        )
        return payload.get("sub")
    except PyJWTError:
        return None
