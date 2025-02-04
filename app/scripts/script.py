import json
import re
import time

from pytube import Playlist
from youtube_transcript_api import YouTubeTranscriptApi

if __name__ == "__main__":
    playlist = Playlist("https://www.youtube.com/playlist?list=PLO-h_HEvT1ysKxfLkI-uk3_vxzxoUHCD7")
    for video_id in playlist:
        match = re.match(
            r'https://www.youtube.com/watch\?v=(?P<video_id>[^"&?\/\s]{11}).*', video_id
        )
        if match:
            video_id = match.groupdict()["video_id"]
        else:
            raise Exception("Could not find video id")

        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        print("save video {video_id} to transcript".format(video_id=video_id))
        with open(f"data/{video_id}.json", "w") as f:
            f.write(json.dumps(transcript))
        time.sleep(10)