import voyageai

from app.database import db_session


def get_db():
    with db_session() as session:
        yield session


def voyageai_client():
    return voyageai.Client()