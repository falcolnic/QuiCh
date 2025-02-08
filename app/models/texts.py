import struct
import uuid

from sqlalchemy import BLOB, JSON, UUID, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from models.base_class import Base


class TranscriptionModel(Base):
    __tablename__ = "transcriptions"

    id = Column(UUID, primary_key=True)
    transcript = Column(String, nullable=False)
    video_id = Column(String, unique=True, nullable=False)

    # One-to-many relationship with DocumentModel
    documents = relationship("DocumentModel", back_populates="transcription")


class DocumentModel(Base):
    __tablename__ = "docs"

    id = Column(UUID, default=uuid.uuid4(), primary_key=True)
    document = Column(String)
    chunk = Column(String)
    llm_chunk = Column(JSON)
    start = Column(Integer)
    duration = Column(Integer)
    chunk_id = Column(String)

    # Foreign key for TranscriptionModel
    video_id = Column(String, ForeignKey("transcriptions.video_id"))
    # One-to-one relationship with TranscriptionModel
    transcription = relationship("TranscriptionModel", back_populates="documents")

    # One-to-many relationship with ChunkModel
    chunks = relationship("ChunkModel", back_populates="document")


class ChunkModel(Base):
    __tablename__ = "chunks"

    id = Column(UUID, default=uuid.uuid4(), primary_key=True)
    title = Column(String)
    source = Column(String)
    context = Column(String)
    start = Column(Integer)
    embedding = Column(BLOB)

    # Foreign key for DocumentModel
    chunk_id = Column(String, ForeignKey("docs.chunk_id"))
    # Many-to-one relationship with DocumentModel
    document = relationship("DocumentModel", back_populates="chunks")

    @property
    def start_time(self):
        return struct.unpack("<Q", self.embedding)[0]

    @classmethod
    def cosine_similarity(cls, a, b):
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x * x for x in a) ** 0.5
        magnitude_b = sum(x * x for x in b) ** 0.5
        return dot_product / (magnitude_a * magnitude_b)

    @classmethod
    def decode(cls, blob):
        return struct.unpack("f" * 512, blob)

    @classmethod
    def encode(cls, values):
        return struct.pack("f" * 512, *values)