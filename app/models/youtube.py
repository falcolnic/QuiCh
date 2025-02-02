from sqlalchemy import UUID, Column, String

from app.models.base_class import Base


class YoutubeModel(Base):
    __tablename__ = "videos"

    id = Column(UUID, primary_key=True)
    transcript = Column(String, nullable=False)
    video_id = Column(String, unique=True, nullable=False)