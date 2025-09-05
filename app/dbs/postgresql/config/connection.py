""" This module establishes a connection to SQLAlchemy based database and creates local session for database """
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# SQLAlchemy connection
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    raise EnvironmentError("The env var 'SQLALCHEMY_DATABASE_URL' is not set.")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=1800,
    # echo=True for debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
