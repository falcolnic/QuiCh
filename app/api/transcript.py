import uuid

from app.api.deps import get_db, voyageai_client
from fastapi import APIRouter, BackgroundTasks, Depends
from app.schemas.transcript import TranscriptSchema, Youtube
from app.services.transcript import calculate_embedding, load_transcript, split_transcript

router = APIRouter()


@router.post("/transcript")
def save_transcript(
    video: Youtube, background_tasks: BackgroundTasks, db=Depends(get_db)
) -> TranscriptSchema:
    transcript = load_transcript(db, video_id=video.video_id)

    return transcript


@router.get("/transcript")
def view_transcript():
    split_transcript(uuid.UUID("9c8bf694-0376-497d-93f6-d72cb2d49215"))


@router.get("/embedding")
def embedding(client=Depends(voyageai_client)):
    calculate_embedding(client)