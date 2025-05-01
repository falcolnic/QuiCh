from typing import Dict, List
from uuid import UUID

from pydantic import BaseModel


class Youtube(BaseModel):
    video_id: str


class TranscriptSchema(BaseModel):
    id: UUID
    transcript: List[Dict]
    video_id: str
    status: str = None
    error: str = None
