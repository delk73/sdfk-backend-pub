"""Database engine setup with tiered fallback logic."""

import os
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.env import load_env
from app.logging import get_logger

logger = get_logger(__name__)

load_env()


def _create_engine(url: str):
    """Create a SQLAlchemy engine with appropriate ``connect_args``."""
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(url, connect_args=connect_args)


# 1. Use DATABASE_URL if provided
DATABASE_URL = os.getenv("DATABASE_URL")
engine = None

if DATABASE_URL:
    try:
        engine = _create_engine(DATABASE_URL)
        logger.info("Using database from env: %s", DATABASE_URL)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to use DATABASE_URL (%s); falling back", exc)
        engine = None

# 2. Default Postgres if no env variable or env failed
if engine is None:
    default_pg = "postgresql://postgres:postgres@localhost:5432/sdfk"
    try:
        engine = _create_engine(default_pg)
        # Attempt a connection to verify driver and server availability
        with engine.connect() as conn:
            conn.execute(sa.select(1))
        logger.info("Using default Postgres DB: %s", default_pg)
    except Exception as exc:
        logger.warning("Postgres unavailable (%s); falling back to SQLite", exc)
        engine = None

# 3. SQLite fallbacks
if engine is None:
    root_dir = Path(__file__).resolve().parent.parent.parent
    sqlite_path = root_dir / "tests" / "data" / "test.db"
    sqlite_url = f"sqlite:///{sqlite_path}"
    try:
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        sqlite_path.touch(exist_ok=True)
        engine = _create_engine(sqlite_url)
        with engine.connect() as conn:
            conn.execute(sa.select(1))
        logger.info("Using file-based SQLite DB: %s", sqlite_url)
    except Exception as exc:
        logger.warning("Failed to use SQLite file (%s); using in-memory DB", exc)
        engine = _create_engine("sqlite:///:memory:")


# Ensure pgvector extension exists for Postgres before creating tables
if engine.dialect.name == "postgresql":
    with engine.connect() as conn:
        conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Yield a SQLAlchemy session and ensure it closes correctly."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Provide quick feedback about which database dialect is in use
logger.info("Database dialect in use: %s", engine.dialect.name)
