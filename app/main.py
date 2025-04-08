import json
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import Depends, FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import ColumnClause, Float, select, text
from starlette.requests import Request

from app.api.deps import get_db, voyageai_client
from app.api.v1 import api_router
from app.database import init_db
from app.jinja_setup import jinja, templates
from app.models.search import SearchModel
from app.models.texts import IdeaModel, YoutubeModel
from app.services.answer import answer_question
from app.services.embeddings import embed

logFormatter = logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s")
log = logging.getLogger()
log.setLevel(logging.INFO)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
log.addHandler(consoleHandler)

TOP_N = 50


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:  # type: ignore
    log.info("Fast API lifespan")
    engine = init_db()
    try:
        yield
    finally:
        log.info("Disposing database engine")
        engine.dispose()


app = FastAPI(
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    lifespan=lifespan,
)

app.include_router(api_router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
@jinja.page("index.jinja2")
def index() -> None:
    """This route serves the index.jinja2 template."""
    ...


@app.get("/blog")
@jinja.page("blog.jinja2")
def blog() -> None:
    """This route serves the blog.jinja2 template."""
    ...


@app.get("/LICENSE")
@jinja.page("LICENSE.jinja2")
def license() -> dict:
    license_text = """The MIT License (MIT) Copyright © 2025 
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
    return {"license": license_text}


@app.get("/version")
def version(db=Depends(get_db)) -> dict:
    return {
        "vss version": db.scalars(text("select vec_version();")),
        "sqlite version": db.scalars(text("select sqlite_version();")),
    }


@app.get("/search")
@jinja.page("search_items.jinja2")
async def search(
    term: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
    client=Depends(voyageai_client),
) -> Dict:
    question_embedding = embed(client, term)
    offset = (page - 1) * page_size

    query = """
        WITH matches AS (
            SELECT rowid, vec_distance_cosine(embedding, :embedding) as distance
            FROM vector_source
            ORDER BY distance
        )
        SELECT ideas.*, matches.distance AS distance
        FROM matches
        LEFT JOIN ideas ON ideas.rowid = matches.rowid
        ORDER BY distance
        LIMIT :page_size OFFSET :offset
    """

    res = db.execute(
        select(IdeaModel, ColumnClause("distance", Float)).from_statement(text(query)),
        {
            "embedding": json.dumps(question_embedding),
            "page_size": page_size,
            "offset": offset,
            "top_n": TOP_N,
        },
    ).all()

    videos_count = len(set(i.video_id for i, _ in res))

    # TODO Use some limit
    total_results = TOP_N
    total_pages = (total_results + page_size - 1) // page_size

    answer = db.scalar(select(SearchModel).filter_by(question=term))
    if answer:
        answer = answer.response
    else:
        answer = answer_question(term, res[:20])
        db.add(SearchModel(id=uuid.uuid4(), question=term, response=answer))
        db.commit()

    return {
        "search_term": term,
        "answer": answer,
        "search_videos_count": videos_count,  # mentions count
        "current_page": page,
        "total_pages": total_pages,
        "docs": [
            (
                round(rank, 4),
                doc,
            )
            for doc, rank in res
        ],
    }


@app.get("/video")
@jinja.page("search_items.jinja2")
def video(video_id: str, db=Depends(get_db)):
    db.sclar(select(YoutubeModel).filter_by(video_id=video_id))


@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: Exception) -> HTMLResponse:
    """This route serves the 404.jinja2 template."""
    return templates.TemplateResponse("404.jinja2", {"request": request})
