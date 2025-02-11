import jwt
import voyageai
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.api.exceptions import credential_exception
from app.config import app_config
from app.database import db_session
from app.schemas.token import TokenPayloadSchema

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{app_config.API_PREFIX}/token")


def get_db():
    with db_session() as session:
        yield session


def voyageai_client():
    return voyageai.Client()


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, app_config.SECRET_KEY, algorithms=[app_config.ALGORITHM])
        token_data = TokenPayloadSchema(**payload)
    except Exception:
        raise credential_exception

    return {"login": token_data.sub}