import pytest
from app.models.db import get_db


def test_get_db_session_provides_valid_session():
    # Get the session from get_db and check it has expected attributes
    db_generator = get_db()
    session = next(db_generator)
    assert hasattr(session, "commit")
    # Clean up (close the session)
    with pytest.raises(StopIteration):
        next(db_generator)


def test_get_db_closes_session(monkeypatch):
    db_generator = get_db()
    session = next(db_generator)
    closed = False

    original_close = session.close

    def fake_close():
        nonlocal closed
        closed = True
        return original_close()

    monkeypatch.setattr(session, "close", fake_close)

    # Exhaust the generator to trigger the finally block (which calls session.close())
    with pytest.raises(StopIteration):
        next(db_generator)

    assert closed is True
