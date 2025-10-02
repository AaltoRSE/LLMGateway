"""This module enables database dependency fetching"""

from typing import Generator
import logging
from sqlalchemy.orm import Session
from ..config.connection import SessionLocal

logger = logging.getLogger("app")


def get_db() -> Generator[Session, None, None]:
    logger.debug("Opening Connection")
    db = SessionLocal()
    try:
        yield db
    finally:
        logger.debug("Closing connection")
        db.close()
