import json
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import Depends, FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import ColumnClause, Float, select, text
from starlette.requests import Request

from app.api.deps import get_db, voyageai_client
from app.api.v1 import api_router
from app.database import init_db
from app.jinja_setup import jinja, templates
from app.middleware.request_logger import RequestLoggerMiddleware
from app.models.search import SearchModel
from app.models.texts import IdeaModel
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
async def lifespan(app: FastAPI):
    log.info("Fast API lifespan starting up")
    engine = init_db()
    try:
        yield
    finally:
        log.info("Disposing database engine")
        if engine is not None:
            engine.dispose()


app = FastAPI(
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    lifespan=lifespan,
)
app.include_router(api_router)

app.mount("/static", StaticFiles(directory="app/static", html=True), name="static")
app.add_middleware(
    RequestLoggerMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

    # TODO Use some limit for non-registered user, if it registered he can make more requests
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


@app.exception_handler(404)
def custom_404_handler(request: Request, exc: Exception) -> HTMLResponse:
    """This route serves the 404.jinja2 template."""
    return templates.TemplateResponse("404.jinja2", {"request": request})
