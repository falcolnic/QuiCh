import sys
from pathlib import Path
import logging

sys.path.append(str(Path(__file__).parent.parent.parent))

from youtube_transcript_api import YouTubeTranscriptApi
from app.database import db_session
from app.models.texts import YoutubeModel, TranscriptionModel
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_transcripts():
    with db_session() as db:
        # Get all videos without transcripts
        videos = db.scalars(
            select(YoutubeModel)
            .outerjoin(YoutubeModel.transcription)
            .where(TranscriptionModel.video_id == None)
        ).all()
        
        logger.info(f"Found {len(videos)} videos without transcripts")
        
        for video in videos:
            try:
                logger.info(f"Processing transcript for {video.video_id}")
                transcript = YouTubeTranscriptApi.get_transcript(video.video_id)
                
                db.add(
                    TranscriptionModel(
                        video_id=video.video_id,
                        transcript=transcript,
                        status="completed"
                    )
                )
                db.commit()
                logger.info(f"Saved transcript for {video.video_id}")
                
            except Exception as e:
                logger.error(f"Error processing {video.video_id}: {str(e)}")
                db.add(
                    TranscriptionModel(
                        video_id=video.video_id,
                        transcript={},
                        status="error",
                        error=str(e)
                    )
                )
                db.commit()

if __name__ == "__main__":
    process_transcripts()
