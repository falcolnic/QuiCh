import uuid
from datetime import timedelta
from typing import Dict, List


def chunk_transcript(video_id, transcript: List[Dict], window_size: int = 10):
    chunks = []
    current_chunks = []
    chunk_duration = 0

    for i, entry in enumerate(transcript):
        if chunk_duration + entry["duration"] > 600:
            chunks.append(
                {
                    "start": current_chunks[0]["start"],
                    "duration": int(chunk_duration),
                    "text": to_text(current_chunks),
                }
            )

            current_chunks = current_chunks[-window_size:] if window_size else []
            chunk_duration = sum(s["duration"] for s in current_chunks)

        current_chunks.append(entry)
        chunk_duration += entry["duration"]

    if chunk_duration > 0:
        if chunk_duration < 300:
            # just append to the last chunk
            chunks[-1]["duration"] += chunk_duration
            chunks[-1]["text"] += to_text(current_chunks)
        else:
            chunks.append(
                {
                    "start": current_chunks[0]["start"],
                    "duration": int(chunk_duration),
                    "text": to_text(current_chunks),
                }
            )

    return {
        "doc_id": video_id,
        "original_uuid": str(uuid.uuid4()),
        "content": " ".join([t["text"] for t in transcript]),
        "chunks": [
            {
                "start": int(c["start"]),
                "content": c["text"],
                "duration": c["duration"],
                "chunk_id": f"{video_id}__chunk_{idx}",
                "original_index": idx,
                "len": len(c["text"]),
            }
            for idx, c in enumerate(chunks)
        ],
    }


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