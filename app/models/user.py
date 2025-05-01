import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.base_class import Base


class UserModel(Base):
    __tablename__ = "users"

    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String, nullable=True)
    username = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    location = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
