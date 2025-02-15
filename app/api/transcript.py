import logging
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends
from app.api.deps import get_db, voyageai_client
from app.schemas.transcript import TranscriptSchema, Youtube
from app.services.ideas_extractor import load_ideas
from app.services.transcript import (
    calculate_idea_embedding, 
    load_all, 
    load_transcript, 
    split_transcript
)

router = APIRouter()

log = logging.getLogger(__name__)


@router.post("/transcript")
def save_transcript(
    video: Youtube, background_tasks: BackgroundTasks, db=Depends(get_db)
) -> TranscriptSchema:
    transcript = load_transcript(db, video_id=video.video_id)

    background_tasks.add_task(split_transcript, transcript.id)

    return transcript


@router.post("/process")
def process_videos(videos: List[str], background_tasks: BackgroundTasks):
    background_tasks.add_task(load_all, videos)


@router.post("/wisdom")
def extract_wisdom(videos: List[str], background_tasks: BackgroundTasks):
    background_tasks.add_task(load_ideas, videos)


@router.get("/embedding")
def embedding(client=Depends(voyageai_client)):
    calculate_idea_embedding(client)