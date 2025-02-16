import logging
import uuid

from pytubefix import Channel
from sqlalchemy import select

from app.database import db_session
from app.models.texts import YOUTUBE_CHAPTER, IdeaModel, YoutubeModel

logger = logging.getLogger(__name__)

c = Channel("https://www.youtube.com/@criticalthinkingpodcast/featured")

print(f"Channel name: {c.channel_name}")
for video in c.videos:
    with db_session() as db:
        print("Load video", video.video_id)
        youtube = db.scalar(select(YoutubeModel).filter_by(video_id=video.video_id))
        if youtube:
            print("Already loaded %s", video.video_id)
        else:
            youtube = YoutubeModel(
                id=uuid.uuid4(),
                video_id=video.video_id,
                title=video.title,
                description=video.description,
                author=video.author,
                publish_date=video.publish_date,
                views=video.views,
                channel_id=video.channel_id,
                channel_url=video.channel_url,
            )
            db.add()

        ides = [
            IdeaModel(
                id=uuid.uuid4(),
                video_id=video.video_id,
                kind=YOUTUBE_CHAPTER,
                idea=c.title,
                start=c.start_seconds,
                end=c.start_seconds + c.duration,
            )
            for c in video.chapters
        ]
        db.add_all(ides)
        db.commit()