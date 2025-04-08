import logging
import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session
from youtube_transcript_api import YouTubeTranscriptApi

from app.database import db_session
from app.models.texts import (
    DocumentModel,
    IdeaModel,
    TranscriptionModel,
    embedding_encode,
)
from app.services.chunker import transcript_first_n_seconds
from app.services.llm_chunks import split_transcript_document

log = logging.getLogger(__name__)


def load_transcript(db: Session, video_id: str):
    transcript = db.scalar(select(TranscriptionModel).filter_by(video_id=video_id))
    if not transcript:
        log.info("Create transcript, load %s", video_id)
        transcript = TranscriptionModel(
            id=uuid.uuid4(),
            video_id=video_id,
            transcript=YouTubeTranscriptApi.get_transcript(video_id),
        )
        db.add(transcript)
        db.commit()

    return transcript


def split_transcript(transcript_id: uuid.UUID, from_start=0):
    with db_session() as db:
        transcript = db.scalar(select(TranscriptionModel).filter_by(id=transcript_id))

        log.info(
            "[%s] Start processing transcript. Duration: %s",
            transcript.video_id,
            transcript.transcript[-1]["start"],
        )

        chunk, is_last = transcript_first_n_seconds(
            transcript.transcript, from_start=from_start
        )

        idx = 0
        while chunk is not None:
            result = []
            log.info(
                "[%s] Processing chunk %s, from start %s",
                transcript.video_id,
                idx,
                from_start,
            )
            idx += 1

            res, usage = split_transcript_document(chunk["text"])
            docs = compile_documents(chunk, res, usage, transcript.video_id)

            log.info("[%s] Create %s docs", transcript.video_id, len(docs))

            if len(docs) > 2:
                result += docs[:-1]
                from_start = docs[-1].start
            else:
                result += docs[:-1]
                from_start = docs[-1].start + docs[-1].duration

            db.add_all(result)
            db.commit()
            if is_last:
                break

            chunk, is_last = transcript_first_n_seconds(
                transcript.transcript, from_start
            )

        log.info("[%s] Done processing transcript", transcript.video_id)


def find_time_point(start: int, timestamps_json: dict, max_offset=3):
    if start in timestamps_json:
        return start

    log.warning(f"Timestamp `{start}` not present, attempting nearby points.")

    for offset in range(1, max_offset + 1):
        if start - offset in timestamps_json:
            log.warning(f"Timestamp found at {start - offset}, offset by -{offset}")
            return start - offset
        if start + offset in timestamps_json:
            log.warning(f"Timestamp found at {start + offset}, offset by +{offset}")
            return start + offset

    raise ValueError(
        f"Cannot find start {start} or nearby points within +/- {max_offset} in {timestamps_json}"
    )


def compile_documents(chunk, res, usage, video_id):
    text_json = {int(c["start"]): c for c in chunk["text_json"]}
    docs = []
    for d in res.docs:
        try:
            assert d.start < d.end, "Assert end is bigger than"
            d.start = find_time_point(d.start, text_json)
            d.end = find_time_point(d.end, text_json)
        except AssertionError as ex:
            log.error(
                "Cannot find timestamp star:`%s` end:`%s` in the json: %s",
                d.start,
                d.end,
                text_json,
            )
            raise ex

        chunks = [
            chunk for start, chunk in text_json.items() if d.start <= start < d.end
        ]
        docs.append(
            DocumentModel(
                id=uuid.uuid4(),
                title=d.title,
                summary=d.context,
                source=" ".join([c["text"] for c in chunks]),
                source_json=chunks,
                llm_metadata=usage,
                start=d.start,
                duration=d.end - d.start,
                video_id=video_id,
            )
        )
    return docs


def calculate_doc_embedding(client):
    with db_session() as db:
        docs = db.scalars(
            select(DocumentModel).where(DocumentModel.source_embedding is None)
        ).all()
        for idx, d in enumerate(docs):
            log.info(
                "[%s/%s]Processing document %s",
                idx,
                len(docs),
                d.title,
            )
            embeddings = client.embed(
                [d.title, d.summary, d.source], model="voyage-3-lite"
            ).embeddings
            d.title_embedding = embedding_encode(embeddings[0])
            d.summary_embedding = embedding_encode(embeddings[1])
            d.source_embedding = embedding_encode(embeddings[2])
            db.commit()


def calculate_idea_embedding(client):
    with db_session() as db:
        batch_size = 100
        offset = 0

        while True:
            word_count = func.length(IdeaModel.idea) - func.length(
                func.replace(IdeaModel.idea, " ", "")
            )

            docs = db.scalars(
                select(IdeaModel)
                .where(word_count > 20)
                .where(IdeaModel.embedding is None)
                .offset(offset)
                .limit(batch_size)
            ).all()

            # Break if no documents are left
            if not docs:
                break
            log.info("Process %s docs", len(docs))

            texts = [d.idea for d in docs]
            embeddings = client.embed(texts, model="voyage-3-lite").embeddings

            for e, d in zip(embeddings, docs):
                d.embedding = embedding_encode(e)
            db.commit()

            # Move to the next batch
            offset += batch_size


def load_all(videos):
    for idx, v in enumerate(videos):
        log.info("[%s/%s] Process: %s", idx, len(videos), v)
        with db_session() as db:
            transcript = load_transcript(db, video_id=v)

            try:
                if transcript.status == "COMPLETED":
                    log.info("%s - already done", transcript.video_id)
                    # continue

                from_start = 0
                if transcript.status == "ERROR":
                    doc = db.scalar(
                        select(DocumentModel)
                        .filter_by(video_id=transcript.video_id)
                        .order_by(desc(DocumentModel.start))
                    )
                    from_start = doc.start if doc else 0

                split_transcript(transcript.id, from_start=from_start)

                transcript.status = "COMPLETED"
                db.commit()

            except Exception as e:
                transcript.status = "ERROR"
                transcript.error = str(e)
                log.error(
                    "[%s/%s] Process: %s. ERROR: %s",
                    idx,
                    len(videos),
                    v,
                    e,
                )
            db.commit()
