import json
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import ColumnClause, Float, select, text
from starlette.requests import Request

from app.api.deps import get_db, voyageai_client
from app.api.sorting import SortOption, get_search_query, get_sort_display_name
from app.api.v1 import api_router
from app.auth.rate_limit import (
    RateLimitExceededException,
    check_rate_limit,
    get_remaining_requests,
)
from app.auth.service import get_user_from_request
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

limiter = Limiter(key_func=get_remote_address)


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
app.state.limiter = limiter

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
    request: Request,
    term: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: SortOption = Query(SortOption.RELEVANCE),
    db=Depends(get_db),
    client=Depends(voyageai_client),
) -> Dict:
    user_info = get_user_from_request(request)
    client_ip = request.client.host

    check_rate_limit(client_ip, user_info["authenticated"])
    rate_info = get_remaining_requests(client_ip, user_info["authenticated"])

    question_embedding = embed(client, term)
    offset = (page - 1) * page_size

    query = get_search_query(sort)

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
        "sort": sort,
        "sort_display_name": get_sort_display_name(sort),
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


@app.exception_handler(RateLimitExceededException)
async def rate_limit_handler(request: Request, exc: RateLimitExceededException):
    return templates.TemplateResponse(
        "rate_limit_exceeded.jinja2",
        {
            "request": request,
            "error_message": exc.message,
            "limit_info": "Unregistered users are limited to 5 searches per day.",
            "retry_info": "Try again tomorrow or create an account for unlimited searches.",
        },
        status_code=429,
    )
