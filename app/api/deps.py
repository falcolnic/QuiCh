import asyncio

import jwt
import voyageai
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.api.exceptions import credential_exception
from app.config import app_config
from app.database import SessionLocal
from app.schemas.token import TokenPayloadSchema

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{app_config.API_PREFIX}/token")

semaphore = asyncio.Semaphore(20)


async def get_db():
    # First, it should be noted that db = SessionLocal() is a non-blocking operation.
    # Prior to the deadlock, all N requests will be able to create a session object and yield it to the path operation.
    # However, `db.scalars(select(UserModel)).all()` is a blocking operation.
    # This means that 100 requests will be able to check out a connection,
    # while our pool with 20 connections (see database.py) will block on `db.query` waiting for a connection to become available.
    # See more https://github.com/tiangolo/fastapi/issues/3205

    # The idea of this fix is to limit the number of opened connections by asyncio.Semaphore
    async with semaphore:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()


def voyageai_client():
    # Initialize the voyageai.Client without the 'proxies' argument
    return voyageai.Client()


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, app_config.SECRET_KEY, algorithms=[app_config.ALGORITHM])
        token_data = TokenPayloadSchema(**payload)
    except Exception:
        raise credential_exception

    return {"login": token_data.sub}
