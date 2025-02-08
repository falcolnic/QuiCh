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
