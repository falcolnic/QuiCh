import logging
import os
from typing import List

from api.deps import get_db, voyageai_client
from fastapi import Depends, FastAPI
from fasthx import Jinja
from models.texts import ChunkModel
from pydantic import BaseModel
from services.embeddings import embed
from sqlalchemy import select
from starlette.templating import Jinja2Templates

logFormatter = logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s")
log = logging.getLogger()
log.setLevel(logging.INFO)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
log.addHandler(consoleHandler)

app = FastAPI(openapi_url="/api/openapi.json", docs_url="/api/docs")


class Search(BaseModel):
    search: str


basedir = os.path.abspath(os.path.dirname(__file__))

# Create the app instance.
app = FastAPI()
# app.mount("/public", StaticFiles(directory="public"), name="public")
# Create a FastAPI Jinja2Templates instance. This will be used in FastHX Jinja instance.
templates = Jinja2Templates(directory=os.path.join(basedir, "templates"))

# FastHX Jinja instance is initialized with the Jinja2Templates instance.
jinja = Jinja(templates)


@app.get("/")
@jinja.page("index.jinja2")
def index() -> None:
    """This route serves the index.html template."""
    ...


@app.get("/search")
@jinja.page("search_items.jinja2")
def search(term: str, db=Depends(get_db), client=Depends(voyageai_client)) -> List:
    question_embedding = embed(client, term)

    rank = []
    for chunk in db.scalars(select(ChunkModel).where(ChunkModel.embedding is not None)):
        similarity = ChunkModel.cosine_similarity(
            ChunkModel.decode(chunk.embedding), question_embedding
        )
        rank.append(
            {
                "similarity": round(similarity, 4),
                "chunk": chunk,
            }
        )
    rank = sorted(rank, key=lambda x: x["similarity"], reverse=True)
    log.info("Len %d", len(rank))
    return rank[:10]

