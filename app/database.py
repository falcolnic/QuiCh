import logging
import sqlite3
from pathlib import Path

import sqlite_vec
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

log = logging.getLogger(__name__)


def setup_database():
    db_path = Path("/data") / "franken.db"
    return create_engine(f"sqlite:///{db_path}", pool_size=20, max_overflow=0)


engine = setup_database()


def init_db() -> None:
    @event.listens_for(engine, "connect")
    def receive_connect(connection, _) -> None:
        log.info("Load SQlite VSS extension")

        connection.enable_load_extension(True)
        sqlite_vec.load(connection)
        connection.enable_load_extension(False)

        (vec_version,) = connection.execute("select vec_version()").fetchone()
        log.info(f"Register extension: vec_version={vec_version}")

        connection.rollback()

        try:
            log.info("Drop virtual tables for embeddings")
            connection.execute("DROP TABLE IF EXISTS vector_source")

            log.info("Create virtual vector tables for embeddings")
            connection.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS vector_source USING vec0(embedding float[512])"
            )

            log.info("Load embeddings into virtual vector table")
            connection.execute(
                """
                INSERT INTO vector_source (rowid, embedding) 
                SELECT rowid, embedding 
                FROM ideas 
                WHERE embedding is not null
            """
            )

            connection.commit()
            log.info("Vector table setup completed successfully")

        except sqlite3.OperationalError as e:
            log.error(f"Error during vector table setup: {e}")


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class db_session:
    def __init__(self):
        self.db = None

    def __enter__(self):
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
