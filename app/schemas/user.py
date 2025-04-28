from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegisterSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    username: str = Field(..., min_length=2, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=20)


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str


class UserResponseSchema(BaseModel):
    uuid: UUID
    name: str
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
