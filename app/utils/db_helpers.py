import time
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, ProgrammingError
from app.logging import get_logger

# Assuming get_logger is available globally or handled elsewhere.
# If it was specific to the old utils.py, this might need adjustment.
# For now, let's use standard logging.
logger = get_logger(__name__)


def wait_for_db(
    db_url: str,
    retries: int = 5,
    delay: float = 1.0,
    simulate_error: bool = False,
    suppress_logs: bool = False,
):
    """Wait for database to be ready
    simulate_error: if True, simulate a database failure for testing the zero-retry branch.
    suppress_logs: if True, do not log warning/error messages or print success messages.
    """
    # Skip wait for SQLite (testing)
    if db_url.startswith("sqlite"):
        return True

    # If no retries are requested, attempt once and return False on failure.
    if retries == 0:
        try:
            if simulate_error:
                raise OperationalError(
                    "Simulated failure", {}, Exception("Simulated error")
                )
            engine = create_engine(db_url)
            with engine.connect() as conn:
                conn.execute(sa.select(1))
            if not suppress_logs:
                logger.info("Database ready!")
            return True
        except (OperationalError, ProgrammingError):
            if not suppress_logs:
                logger.error(
                    "Database connection failed with no retries.", exc_info=True
                )
            return False
    else:
        for attempt in range(retries):
            try:
                engine = create_engine(db_url)
                with engine.connect() as conn:
                    conn.execute(sa.select(1))
                if not suppress_logs:
                    logger.info("Database ready!")
                return True
            except (OperationalError, ProgrammingError) as e:
                if attempt < retries - 1:
                    if not suppress_logs:
                        logger.warning(
                            f"Database not ready. Retrying in {delay} seconds... ({str(e)})"
                        )
                    time.sleep(delay)
                else:
                    if not suppress_logs:
                        logger.error(
                            "Database connection failed after retries.", exc_info=True
                        )
                    raise e


# It seems create_engine is imported from sqlalchemy, not defined in utils.py
# If there were other db related helper functions, they would go here.
# For now, this file will primarily hold wait_for_db.
