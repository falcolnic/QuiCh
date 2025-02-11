# models.py

# Base class for our models
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def setup_database():
    """
    Set up the SQLite database and create all tables based on models.
    """
    return create_engine("sqlite:///franken.db")


# Initialize the database
engine = setup_database()

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