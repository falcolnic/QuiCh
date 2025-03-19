from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayloadSchema(BaseModel):
    exp: Optional[int] = None
    sub: Optional[str] = None
    type: Optional[str] = None
    iat: Optional[datetime] = None