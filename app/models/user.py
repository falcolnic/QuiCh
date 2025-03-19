from sqlalchemy import Boolean, Column, String
from app.models.base_class import Base

class UserModel(Base):
    __tablename__ = "users"
    
    username = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)