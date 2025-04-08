import struct
import time
import uuid

from sqlalchemy import BLOB, JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base_class import Base
from app.models.custom_types import UUID_as_Integer


class YoutubeModel(Base):
    __tablename__ = "youtube"

    id = Column(UUID_as_Integer, primary_key=True)
    video_id = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    author = Column(String)
    publish_date = Column(DateTime)
    channel_id = Column(String)
    channel_url = Column(String)
    views = Column(Integer)

    # One-to-one relationship with TranscriptionModel
    transcription = relationship("TranscriptionModel", back_populates="youtube", uselist=False)
    # One-to-many relationship with DocumentModel
    ideas = relationship("IdeaModel", back_populates="youtube")

    @property
    def views_h(self) -> str:
        if self.views >= 1_000_000:
            return f"{self.views / 1_000_000:.1f}M"
        elif self.views >= 1_000:
            return f"{self.views / 1_000:.1f}K"
        else:
            return str(self.views)


class TranscriptionModel(Base):
    __tablename__ = "transcriptions"

    id = Column(UUID_as_Integer, primary_key=True)
    transcript = Column(JSON, nullable=False)
    video_id = Column(String, ForeignKey("youtube.video_id"), unique=True, nullable=False)
    status = Column(String, nullable=True)
    error = Column(String, nullable=True)

    # One-to-one relationship with YoutubeModel
    youtube = relationship("YoutubeModel", back_populates="transcription")
    # One-to-many relationship with DocumentModel
    documents = relationship("DocumentModel", back_populates="transcription")


class DocumentModel(Base):
    __tablename__ = "docs"

    id = Column(UUID_as_Integer, default=uuid.uuid4(), primary_key=True)

    title = Column(String)
    source = Column(String)
    source_json = Column(JSON)
    llm_metadata = Column(JSON)
    summary = Column(String)

    start = Column(Integer)
    duration = Column(Integer)

    title_embedding = Column(BLOB)
    summary_embedding = Column(BLOB)
    source_embedding = Column(BLOB)
    total_embedding = Column(BLOB)

    # Foreign key for TranscriptionModel
    video_id = Column(String, ForeignKey("transcriptions.video_id"))

    # One-to-one relationship with TranscriptionModel
    transcription = relationship("TranscriptionModel", back_populates="documents")


YOUTUBE_CHAPTER = "youtube_chapter"


class IdeaModel(Base):
    __tablename__ = "ideas"

    id = Column(UUID_as_Integer, default=uuid.uuid4(), primary_key=True)

    idea = Column(String)
    start = Column(Integer)
    end = Column(Integer)
    embedding = Column(BLOB)
    kind = Column(String)

    video_id = Column(String, ForeignKey("youtube.video_id"))
    # One-to-one relationship with TranscriptionModel
    youtube = relationship("YoutubeModel", back_populates="ideas")

    @property
    def start_h(self):
        return time.strftime("%H:%M:%S", time.gmtime(self.start))


def embedding_decode(blob):
    return struct.unpack("f" * 512, blob)


def embedding_encode(values):
    return struct.pack("f" * 512, *values)
