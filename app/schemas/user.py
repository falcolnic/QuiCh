import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegisterSchema(BaseModel):
    username: str = Field(
        ...,
        min_length=2,
        max_length=20,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Username must be 2-20 characters and contain only letters, numbers, underscores, or hyphens",
    )
    email: EmailStr = Field(..., description="A valid email address")
    password: str = Field(
        ..., min_length=8, max_length=20, description="Password must be 8-20 characters"
    )
    ip_address: str | None = None
    location: str | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username must contain only letters, numbers, underscores, or hyphens"
            )
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if " " in v:
            raise ValueError("Password cannot contain spaces")
        return v


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str
    ip_address: str | None = None
    location: str | None = None


class UserResponseSchema(BaseModel):
    uuid: UUID
    name: str | None = None
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime
    ip_address: str | None = None
    location: str | None = None

    model_config = ConfigDict(from_attributes=True)
