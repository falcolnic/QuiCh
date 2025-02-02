import uuid

from fasthtml.common import *
from sqlalchemy import select
from youtube_transcript_api import YouTubeTranscriptApi

from app.components.js import javascripts
from app.components.navbar import home_template
from app.database import db_session
from app.models.youtube import YoutubeModel

youtube_app, rt = fast_app(pico=False, hdrs=javascripts)


@youtube_app.get("/youtube")
async def view_video(request: Request):
    return home_template(request)


@youtube_app.post("/youtube")
async def store_video(request: Request, video_id: str):
    match = re.match(r'https://www.youtube.com/watch\?v=(?P<video_id>[^"&?\/\s]{11}).*', video_id)
    if match:
        video_id = match.groupdict()["video_id"]
    else:
        return home_template(request), P("Can't find video id")

    with db_session() as db:
        video = db.scalar(select(YoutubeModel).filter_by(video_id=video_id))

        if video is None:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            transcript = "\n".join([t["text"] for t in transcript])

            video = YoutubeModel(
                id=uuid.uuid4(),
                video_id=video_id,
                transcript=transcript,
            )
            db.add(video)
            db.commit()
            db.flush()

        return home_template(request), video.knowledge