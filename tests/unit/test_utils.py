import pytest
import time
from sqlalchemy.exc import OperationalError
import logging

# from app import utils # No longer need to import the whole utils package for patching
from app.utils.db_helpers import wait_for_db  # Import wait_for_db directly

# For monkeypatching, we'll use the string path to where create_engine is defined or imported
# in the module under test (app.utils.db_helpers)

# Dummy connection and engine classes for success simulation


class DummyResult:
    def scalar(self):
        return 1


class DummyConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def execute(self, cmd):
        return DummyResult()

    def commit(self):
        pass


class DummyEngine:
    def connect(self):
        return DummyConnection()


def dummy_create_engine_success(db_url):
    return DummyEngine()


def dummy_create_engine_failure(db_url):
    raise OperationalError("dummy", "dummy", "Connection failed")


def test_wait_for_db_success(monkeypatch):
    # Override create_engine in the db_helpers module
    monkeypatch.setattr(
        "app.utils.db_helpers.create_engine", dummy_create_engine_success
    )

    start = time.time()
    # Use the directly imported wait_for_db
    result = wait_for_db("postgres://localhost:5432/dbname", retries=1, delay=0)
    end = time.time()
    assert result is True
    assert end - start < 1


def test_wait_for_db_timeout(monkeypatch):
    # Override create_engine in the db_helpers module
    monkeypatch.setattr(
        "app.utils.db_helpers.create_engine", dummy_create_engine_failure
    )

    with pytest.raises(OperationalError, match="Connection failed"):
        wait_for_db(
            "postgres://localhost:5432/dbname", retries=2, delay=0, suppress_logs=True
        )


def test_wait_for_db_no_retries(monkeypatch):
    """Test behavior when no retries are allowed"""
    # Test success case
    monkeypatch.setattr(
        "app.utils.db_helpers.create_engine", dummy_create_engine_success
    )
    assert (
        wait_for_db(
            "postgresql://postgres:postgres@localhost:5432/test",
            retries=0,
            suppress_logs=True,
        )
        is True
    )

    # Test failure case
    monkeypatch.setattr(
        "app.utils.db_helpers.create_engine", dummy_create_engine_failure
    )
    assert (
        wait_for_db(
            "postgresql://invalid:invalid@localhost:5432/invalid",
            retries=0,
            suppress_logs=True,
        )
        is False
    )


def test_wait_for_db_with_retries(monkeypatch):
    """Test behavior with retries"""
    # Test success case
    monkeypatch.setattr(
        "app.utils.db_helpers.create_engine", dummy_create_engine_success
    )
    assert (
        wait_for_db(
            "postgresql://postgres:postgres@localhost:5432/test",
            retries=3,
            delay=0.1,
            suppress_logs=True,
        )
        is True
    )

    # Test failure case
    monkeypatch.setattr(
        "app.utils.db_helpers.create_engine", dummy_create_engine_failure
    )
    with pytest.raises(OperationalError):
        wait_for_db(
            "postgresql://invalid:invalid@localhost:5432/invalid",
            retries=2,
            delay=0.1,
            suppress_logs=True,
        )


def test_wait_for_db_with_retries_failure(monkeypatch, caplog):
    monkeypatch.setattr(
        "app.utils.db_helpers.create_engine", dummy_create_engine_failure
    )
    with caplog.at_level(logging.ERROR):
        with pytest.raises(OperationalError):
            # Use the directly imported wait_for_db
            wait_for_db("postgres://localhost:5432/dbname", retries=3, delay=0)
        assert "Database connection failed after retries." in caplog.text


def test_wait_for_db_with_retries_partial_failure(monkeypatch, caplog):
    call_count = 0

    def dummy_create_engine_partial_failure(db_url):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise OperationalError("dummy", "dummy", "Connection failed")
        return DummyEngine()

    monkeypatch.setattr(
        "app.utils.db_helpers.create_engine", dummy_create_engine_partial_failure
    )
    with caplog.at_level(logging.WARNING):
        # Use the directly imported wait_for_db
        result = wait_for_db("postgres://localhost:5432/dbname", retries=3, delay=0)
        assert result is True
        assert "Database not ready. Retrying in 0 seconds..." in caplog.text


def test_wait_for_db_suppress_logs(monkeypatch, caplog):
    monkeypatch.setattr(
        "app.utils.db_helpers.create_engine", dummy_create_engine_failure
    )
    with caplog.at_level(logging.ERROR):
        # Use the directly imported wait_for_db
        result = wait_for_db(
            "postgres://localhost:5432/dbname", retries=0, delay=0, suppress_logs=True
        )
        assert result is False
        assert "Database connection failed with no retries." not in caplog.text


def test_wait_for_db_with_retries_success(monkeypatch):
    monkeypatch.setattr(
        "app.utils.db_helpers.create_engine", dummy_create_engine_success
    )
    # Use the directly imported wait_for_db
    result = wait_for_db("postgres://localhost:5432/dbname", retries=3, delay=0)
    assert result is True


def test_wait_for_db_sqlite():
    """Test that SQLite connections return immediately"""
    assert wait_for_db("sqlite:///test.db", suppress_logs=True) is True


def test_wait_for_db_no_retries_success(monkeypatch):
    monkeypatch.setattr(
        "app.utils.db_helpers.create_engine", dummy_create_engine_success
    )
    # Use the directly imported wait_for_db
    result = wait_for_db("postgres://localhost:5432/dbname", retries=0, delay=0)
    assert result is True


def test_wait_for_db_no_retries_failure(monkeypatch):
    monkeypatch.setattr(
        "app.utils.db_helpers.create_engine", dummy_create_engine_failure
    )
    # Use the directly imported wait_for_db
    result = wait_for_db("postgres://localhost:5432/dbname", retries=0, delay=0)
    assert result is False


def test_wait_for_db_no_retries_simulate_error(monkeypatch):
    # This test variant checks the simulate_error flag within wait_for_db,
    # which raises an error *before* create_engine is called. So, no patch needed for create_engine here.
    # However, the original test_utils.py had monkeypatch.setattr(utils, "create_engine", dummy_create_engine_success)
    # which implies it expected create_engine to be potentially called if simulate_error was False. This logic is fine.
    # The simulate_error=True path should cause an early exit or specific error.
    # In wait_for_db, if simulate_error is True and retries == 0, it raises internally then returns False.
    result = wait_for_db(
        "postgres://localhost:5432/dbname", retries=0, delay=0, simulate_error=True
    )
    assert result is False


def test_wait_for_db_simulated_error():
    """Test simulated error handling"""
    # This test doesn't mock create_engine because simulate_error=True in wait_for_db
    # should trigger an internal OperationalError if retries > 0, or return False if retries == 0.
    # The actual create_engine from sqlalchemy won't be called if simulate_error path is hit first.
    assert (
        wait_for_db(
            "postgresql://postgres:postgres@localhost:5432/test",
            retries=0,
            simulate_error=True,
            suppress_logs=True,
        )
        is False
    )

    with pytest.raises(OperationalError):
        wait_for_db(
            "postgresql://postgres:postgres@localhost:5432/test",
            retries=2,
            delay=0.1,
            simulate_error=True,
            suppress_logs=True,
        )
