from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayloadSchema(BaseModel):
    exp: Optional[int] = None
    sub: Optional[str] = None
    uuid: Optional[UUID] = None
    type: Optional[str] = None
    iat: Optional[datetime] = None


class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
