# models.py
import logging

import sqlite_vec
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Base class for our models

log = logging.getLogger(__name__)


def setup_database():
    """
    Set up the SQLite database and create all tables based on models.
    """
    return create_engine("sqlite:///franken.db", pool_size=20, max_overflow=0)


# Initialize the database
engine = setup_database()


def init_db() -> None:
    @event.listens_for(engine, "connect")
    def receive_connect(connection, _) -> None:
        log.info("Load SQlite VEC extension")

        connection.enable_load_extension(True)
        sqlite_vec.load(connection)
        connection.enable_load_extension(False)

        (vec_version,) = connection.execute("select vec_version()").fetchone()
        log.info(f"Register extension: vec_version={vec_version}")

        log.info("Create virtual vector table for embeddings")
        connection.execute(
            """
CREATE VIRTUAL TABLE IF NOT EXISTS vec_articles USING vec0(
    document_id integer primary key,
    contents_embedding float[768]
);
"""
        )
        connection.commit()


# Create a new session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class db_session:
    def __init__(self):
        self.db = None

    def __enter__(self):
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()