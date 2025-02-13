import json
import logging
import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI
from fasthx import Jinja
from sqlalchemy import ColumnClause, Float, select, text
from starlette.templating import Jinja2Templates

from app.api.deps import get_db, voyageai_client
from app.api.v1 import api_router
from app.database import init_db
from app.models.texts import ChunkModel
from app.services.embeddings import embed

logFormatter = logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s")
log = logging.getLogger()
log.setLevel(logging.INFO)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
log.addHandler(consoleHandler)


@asynccontextmanager
async def lifespan(app: FastAPI) -> None: # type: ignore
    log.info("Fast API lifespan")
    init_db()
    yield


app = FastAPI(openapi_url="/api/openapi.json", docs_url="/api/docs", lifespan=lifespan)


basedir = os.path.abspath(os.path.dirname(__file__))

# Create the app instance.
app.include_router(api_router)
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


@app.get("/version")
def version(db=Depends(get_db)) -> dict:
    return {
        "vec version": db.scalars(text("select vec_version();")),
        "sqlite version": db.scalars(text("select sqlite_version();")),
    }

@app.get("/search")
@jinja.page("search_items.jinja2")
def search(term: str, db=Depends(get_db), client=Depends(voyageai_client)) -> List:
    question_embedding = embed(client, term)

    query = f"""
        with matches as (
            select rowid, distance
            from vss_articles
            where vss_search(description_embedding,
            vss_search_params(json('{json.dumps(question_embedding)}'), 20)
            )
        )
        select chunks.*, matches.distance as distance
        from matches
        left join chunks on chunks.rowid = matches.rowid
"""


    res = db.execute(
        select(ChunkModel, ColumnClause("distance", Float)).from_statement(text(query))
    ).all()

    return [
        {
            "similarity": round(similarity, 4),
            "chunk": chunk,
        }
        for chunk, similarity in res
    ]