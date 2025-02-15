from app.models.base_class import Base
from app.models.custom_types import UUID_as_Integer
from sqlalchemy import Column, String


class SearchModel(Base):
    __tablename__ = "searches"

    id = Column(UUID_as_Integer, primary_key=True)
    question = Column(String)
    response = Column(String)