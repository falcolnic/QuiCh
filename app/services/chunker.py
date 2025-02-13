from datetime import timedelta
from typing import Dict, List


def transcript_first_n_seconds(transcript: List[Dict], from_start: int = 0, first_seconds: int = 600):
    current_chunks = []
    chunk_duration = 0

    for i, entry in enumerate(transcript):
        if entry["start"] < from_start:
            continue

        if chunk_duration + entry["duration"] > first_seconds:
            return {
                "start": current_chunks[0]["start"],
                "duration": int(chunk_duration),
                "text": to_text(current_chunks),
                "text_json": current_chunks,
            }, False

        current_chunks.append(entry)
        chunk_duration += entry["duration"]

    if current_chunks:
        return {
            "start": current_chunks[0]["start"],
            "duration": int(chunk_duration),
            "text": to_text(current_chunks),
            "text_json": current_chunks,
        }, True
    else:
        return None

def to_text(current_chunks):
    text = ""
    for idx, chunk in enumerate(current_chunks):
        if idx % 5 == 0:
            text += " " + f"[{int(chunk['start'])}s]" + " " + chunk["text"]
        else:
            text += " " + chunk["text"]
    return text


def seconds_to_time(seconds):
    return "[" + str(timedelta(seconds=int(seconds))) + "]"