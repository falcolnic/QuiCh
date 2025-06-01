import asyncio

import jwt
import voyageai
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config import app_config
from app.database import SessionLocal
from app.schemas.token import TokenPayloadSchema

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{app_config.API_PREFIX}/token")

semaphore = asyncio.Semaphore(20)


async def get_db():
    async with semaphore:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()


def voyageai_client():
    return voyageai.Client()


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(
            token,
            app_config.SECRET_KEY,
            algorithms=[app_config.ALGORITHM],
        )
        token_data = TokenPayloadSchema(**payload)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"login": token_data.sub, "uuid": token_data.uuid}
