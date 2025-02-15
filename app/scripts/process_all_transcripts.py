import sys
from pathlib import Path
import logging

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.database import db_session
from app.models.texts import YoutubeModel, TranscriptionModel
from app.services.transcript import load_all
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_all_transcripts():
    with db_session() as db:
        # Get all video IDs that don't have completed transcriptions
        videos = db.scalars(
            select(YoutubeModel.video_id)
            .outerjoin(YoutubeModel.transcription)
            .where(
                (TranscriptionModel.status != "COMPLETED") | 
                (TranscriptionModel.video_id == None)
            )
        ).all()
        
        logger.info(f"Found {len(videos)} videos to process")
        if not videos:
            logger.info("All videos are already processed!")
            return
            
        # Process using existing service
        load_all(videos)

if __name__ == "__main__":
    process_all_transcripts()
