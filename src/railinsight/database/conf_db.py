import os

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.engine import Engine

load_dotenv()


def make_engine() -> Engine:
    """Create a SQLAlchemy engine for the configured PostgreSQL database.

    Returns:
        A database engine built from environment variables.
    """

    url_object = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
    )
    engine = create_engine(url=url_object, pool_pre_ping=True)
    return engine
