from fastapi import APIRouter, Depends
from sqlalchemy import select, text

from app.api.deps import get_db
from app.jinja_setup import jinja
from app.models.texts import YoutubeModel

router = APIRouter()


@router.get("/")
@jinja.page("index.jinja2")
async def index() -> None:
    """This route serves the index.jinja2 template."""
    ...


@router.get("/blog")
@jinja.page("blog.jinja2")
async def blog() -> None:
    """This route serves the blog.jinja2 template."""
    ...


@router.get("/video")
@jinja.page("search_items.jinja2")
async def video(video_id: str, db=Depends(get_db)):
    db.scalar(select(YoutubeModel).filter_by(video_id=video_id))


@router.get("/LICENSE")
@jinja.page("LICENSE.jinja2")
async def license() -> dict:
    license_text = """The MIT License (MIT) Copyright © 2025 
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
    return {"license": license_text}


@router.get("/version")
async def version(db=Depends(get_db)) -> dict:
    return {
        "vss version": db.scalars(text("select vec_version();")),
        "sqlite version": db.scalars(text("select sqlite_version();")),
    }
