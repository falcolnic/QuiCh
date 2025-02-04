import glob
import json
import logging
import uuid

from sqlalchemy import select

from app.database import db_session
from app.models.texts import DocumentModel
from app.services.chunker import chunk_transcript
from app.services.llm_chunks import split_transcript_document

logFormatter = logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s")
log = logging.getLogger()
log.setLevel(logging.INFO)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
log.addHandler(consoleHandler)


def main():
    # Load the JSON data
    # load_transcript_into_db()

    with db_session() as db:
        for doc in db.scalars(select(DocumentModel)):
            log.info("Processing document %s", doc.chunk_id)
            if doc.llm_chunk:
                continue

            llm_chunk = split_transcript_document(doc.chunk)
            doc.llm_chunk = llm_chunk
            db.commit()
            db.flush(doc)


def load_transcript_into_db():
    files = glob.glob("data/*.json")
    for idx, transcript_file in enumerate(files):
        if transcript_file.endswith("all.json"):
            continue

        with open(transcript_file, "r") as f:
            video_id = transcript_file.split("/")[-1].split(".")[0]

            log.info(f"[{idx}/{len(files)}]Process: {video_id}")

            # Process the transcript
            transcript = json.load(f)
            chunks = chunk_transcript(video_id, transcript)
            with db_session() as db:
                for chunk in chunks["chunks"]:
                    db.add(
                        DocumentModel(
                            id=uuid.uuid4(),
                            video_id=video_id,
                            chunk=chunk["content"],
                            start=chunk["start"],
                            duration=chunk["duration"],
                            chunk_id=chunk["chunk_id"],
                        )
                    )

                db.commit()


if __name__ == "__main__":
    main()