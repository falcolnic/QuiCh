import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import select

from app.database import db_session
from app.models.texts import YoutubeModel


def check_youtube_videos():
    with db_session() as db:
        videos = db.scalars(select(YoutubeModel)).all()

        if not videos:
            print("No videos found in database!")
            return

        print(f"\nFound {len(videos)} videos in database:")
        print("-" * 50)

        for video in videos:
            print(
                f"""
Title: {video.title}
Video ID: {video.video_id}
Views: {video.views}
Author: {video.author}
Published: {video.publish_date}
--------------------------------------------------"""
            )


if __name__ == "__main__":
    check_youtube_videos()
