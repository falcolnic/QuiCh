import json
import re
import uuid
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from app.database import db_session
from app.models.texts import IdeaModel


def fetch_episode_urls(api_url):
    response = requests.get(api_url)
    response.raise_for_status()
    data = response.json()
    return [episode["absolute_url"] for episode in data["episodes"]]


def parse_timestamp(timestamp_str):
    """Convert timestamp (HH:MM:SS.sss) to seconds."""

    timestamp_str = re.sub(r"\.\d*$", "", timestamp_str)
    # Check format: "MM:SS.sss"
    if len(timestamp_str.split(":")) == 2:
        time_parts = datetime.strptime(timestamp_str, "%M:%S")
        delta = timedelta(
            minutes=time_parts.minute,
            seconds=time_parts.second,
            microseconds=time_parts.microsecond,
        )
    # Check format: "HH:MM:SS.sss"
    else:
        time_parts = datetime.strptime(timestamp_str, "%H:%M:%S")
        delta = timedelta(
            hours=time_parts.hour,
            minutes=time_parts.minute,
            seconds=time_parts.second,
            microseconds=time_parts.microsecond,
        )
    return int(delta.total_seconds())


def parse_transcript_caption(caption):
    """Parse individual caption into JSON format."""
    match = re.match(r"^(.*?)\s*\(([\d:.]+)\)(.*)$", caption)
    if not match:
        return None
    speaker = match.group(1).strip()
    timestamp = match.group(2)
    text = match.group(3).strip()
    # start = parse_timestamp(timestamp)
    return {"speaker": speaker, "start": timestamp, "text": text}


def fetch_transcription_text(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    transcript_div = soup.find("div", itemprop="transcript")
    if not transcript_div:
        return None
    paragraphs = transcript_div.find_all("p")
    captions = [parse_transcript_caption(p.get_text(strip=True)) for p in paragraphs]
    return [caption for caption in captions if caption]


def extract_youtube_video_id(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    iframe = soup.find("iframe", src=lambda x: x and "youtube.com/embed/" in x)
    if iframe:
        video_url = iframe["src"]
        video_id = video_url.split("/")[-1]
        return video_id
    return None


def fetch_all_transcriptions_and_videos(api_url):
    urls = fetch_episode_urls(api_url)
    data = {}
    for url in urls:
        print(url)
        transcription = fetch_transcription_text(url)
        video_id = extract_youtube_video_id(url)
        print("extracted video id", video_id)
        data[url] = {"transcription": transcription, "video_id": video_id}
    return data


# Example usage
api_url = "https://podpage-api.herokuapp.com/api/13535590657197/episodes/"
# all_data = fetch_all_transcriptions_and_videos(api_url)
with open("./scripts/transcript2.json", "r") as f:
    json_data = json.load(f)
    with db_session() as db:
        for url, t in json_data.items():
            transcription = t["transcription"]
            video_id = t["video_id"]
            print(video_id)
            if not transcription or not video_id:
                print("not ", video_id)
                continue

            ideas = [
                IdeaModel(
                    id=uuid.uuid4(),
                    idea=i["speaker"] + ": " + i["text"],
                    start=parse_timestamp(i["start"]),
                    kind="phrase",
                    video_id=video_id,
                )
                for i in transcription
            ]
            db.add_all(ideas)
        db.commit()