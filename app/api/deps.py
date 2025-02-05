import os

import voyageai

from app.database import db_session


def get_db():
    with db_session() as session:
        yield session


def voyageai_client():
    voyage_api_key = os.getenv("VOYAGE_API_KEY")
    if not voyage_api_key:
        raise ValueError("VOYAGE_API_KEY environment variable is not set")
    return voyageai.Client(api_key=voyage_api_key)