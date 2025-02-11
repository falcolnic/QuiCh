import logging
import os
import uuid

import voyageai
from sqlalchemy import select

from app.database import db_session
from app.models.texts import ChunkModel, DocumentModel
from app.services.llm_chunks import split_document

from dotenv import load_dotenv
load_dotenv()

logFormatter = logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s")

log = logging.getLogger()
log.setLevel(logging.INFO)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
log.addHandler(consoleHandler)


vo = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))

def main():
    # Load the JSON data
    # load_transcript_into_db()

    with db_session() as db:
        for idx, doc in enumerate(
            db.scalars(select(DocumentModel).where(DocumentModel.llm_chunk is not None))
        ):
            log.info("[%d]Processing document %s", idx, doc.chunk_id)
            if not doc.llm_chunk:
                continue

            llm_docs = doc.llm_chunk["docs"]
            docs = split_document(llm_docs, doc.chunk)

            if not docs:
                continue

            embedding = embed(
                [
                    [chunk["title"], chunk["context"], source]
                    for source, chunk in zip(docs, llm_docs)
                ]
            )

            for e, source, chunk in zip(embedding, docs, doc.llm_chunk["docs"]):
                with db_session() as i_db:
                    chunk = ChunkModel(
                        id=uuid.uuid4(),
                        chunk_id=doc.chunk_id,
                        title=chunk["title"],
                        source=source.strip(),
                        context=chunk["context"],
                        start=chunk["start"],
                        embedding=e,
                    )
                    i_db.add(chunk)
                    i_db.commit()

def embed(docs):
    docs = ["\n".join([title, context, source]) for title, context, source in docs]
    embedding = vo.embed(docs, model="voyage-3-lite")
    return [ChunkModel.encode(e) for e in embedding.embeddings]


if __name__ == "__main__":
    main()