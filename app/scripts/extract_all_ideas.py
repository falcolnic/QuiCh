import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import select

from app.database import db_session
from app.models.texts import TranscriptionModel
from app.services.ideas_extractor import load_ideas

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_all_ideas():
    with db_session() as db:
        # Get video IDs with completed transcripts but no ideas
        videos = db.scalars(
            select(TranscriptionModel.video_id)
            .filter_by(status="COMPLETED")
            .outerjoin(TranscriptionModel.ideas)
            .where(TranscriptionModel.ideas == None)
        ).all()
        
        logger.info(f"Found {len(videos)} videos needing idea extraction")
        if not videos:
            logger.info("No new videos to process!")
            return
            
        # Process using existing ideas extractor
        load_ideas(videos)

if __name__ == "__main__":
    extract_all_ideas()
