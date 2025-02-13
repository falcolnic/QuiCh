import logging
import uuid

from app.database import db_session
from app.models.texts import DocumentModel, TranscriptionModel, embedding_encode
from app.services.chunker import transcript_first_n_seconds
from app.services.llm_chunks import split_transcript_document
from sqlalchemy import select
from sqlalchemy.orm import Session
from youtube_transcript_api import YouTubeTranscriptApi

log = logging.getLogger(__name__)


def load_transcript(db: Session, video_id: str):
    log.info("Loading transcript from %s", video_id)

    transcript = db.scalar(select(TranscriptionModel).filter_by(video_id=video_id))
    if not transcript:
        transcript = TranscriptionModel(
            id=uuid.uuid4(),
            video_id=video_id,
            transcript=YouTubeTranscriptApi.get_transcript(video_id),
        )
    else:
        transcript.transcript = YouTubeTranscriptApi.get_transcript(video_id)

    db.add(transcript)
    db.commit()
    return transcript


def split_transcript(transcript_id: uuid.UUID):
    with db_session() as db:
        transcript = db.scalar(select(TranscriptionModel).filter_by(id=transcript_id))

        from_start = 0
        chunk, is_last = transcript_first_n_seconds(transcript.transcript, from_start=from_start)
        idx = 0
        while chunk is not None:
            log.info("Processing chunk %s", idx)
            idx += 1

            res, usage = split_transcript_document(chunk["text"])

            docs = compile_documents(chunk, res, usage, transcript.video_id)
            log.info("Create %s documents", len(docs))

            db.add_all(docs[:-1])
            db.commit()

            log.info("Store %s documents", len(docs) - 1)
            if is_last:
                break

            chunk, is_last = transcript_first_n_seconds(
                transcript.transcript, from_start=docs[-1].start
            )


def compile_documents(chunk, res, usage, video_id):
    text_json = {int(c["start"]): c for c in chunk["text_json"]}
    docs = []
    for d in res.docs:
        try:
            assert d.start in text_json, "Assert start in provided transcript chunk"
            assert d.end in text_json, "Assert end in provided transcript chunk"
            assert d.start < d.end, "Assert end is bigger than"
        except AssertionError as ex:
            log.error(
                "Cannot find timestamp star:`%s` end:`%s` in the json: %s",
                d.start,
                d.end,
                text_json,
            )
            raise ex

        chunks = [chunk for start, chunk in text_json.items() if d.start <= start < d.end]
        docs.append(
            DocumentModel(
                id=uuid.uuid4(),
                title=d.title,
                summary=d.context,
                source=" ".join([c["text"] for c in chunks]),
                source_json=chunks,
                llm_metadata=usage,
                start=d.start,
                duration=d.end,
                video_id=video_id,
            )
        )
    return docs


def calculate_embedding(client):
    with db_session() as db:
        docs = db.scalars(select(DocumentModel))
        for d in docs:
            embeddings = client.embed(
                [d.title, d.summary, d.source], model="voyage-3-lite"
            ).embeddings
            d.title_embedding = embedding_encode(embeddings[0])
            d.summary_embedding = embedding_encode(embeddings[1])
            d.source_embedding = embedding_encode(embeddings[2])
            db.commit()