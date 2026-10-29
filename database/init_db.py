import logging

import db_table
from conf_db import make_engine

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Initialize database and create tables."""

    engine = make_engine()
    try:
        db_table.metadata.create_all(engine)
        logger.info(f"Database {db_table.TABLE_NAME} and tables created successfully")
    except Exception as e:
        logger.error("Database initialization failed: %s", e)
    finally:
        engine.dispose()


if __name__ == "__main__":
    init_db()
