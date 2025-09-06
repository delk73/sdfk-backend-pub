"""Coverage tests for the modulations router focusing on error scenarios."""

from __future__ import annotations

import builtins
from typing import Callable
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import security
from app.main import app
from app.models.db import get_db

app.dependency_overrides[security.verify_jwt] = lambda token=None: {"sub": "test_user"}

client = TestClient(app)


@pytest.fixture
def basic_modulation_data() -> dict:
    """Return basic modulation payload for tests."""
    return {
        "name": "Test Modulation",
        "description": "Test modulation description",
        "meta_info": {"category": "test", "tags": ["test", "coverage"]},
        "modulations": [
            {
                "id": "test_modulation",
                "target": "visual.u_time",
                "type": "additive",
                "waveform": "sine",
                "frequency": 0.5,
                "amplitude": 0.5,
                "offset": 0.0,
                "phase": 0.0,
                "min": 0.0,
                "max": 1.0,
            }
        ],
    }


def _patch_update_setattr_value_error(
    mock_modulation: MagicMock, message: str
) -> patch:
    original_setattr = builtins.setattr

    def mocked(obj, name, value):
        if obj is mock_modulation and name == "name":
            raise ValueError(message)
        return original_setattr(obj, name, value)

    return patch("builtins.setattr", mocked)


@pytest.mark.parametrize(
    "side_effect,expected_status,expected_detail",
    [
        (IntegrityError("stmt", "params", "orig"), 409, "already exists"),
        (SQLAlchemyError("db"), 500, "Internal server error"),
    ],
)
def test_create_modulation_db_errors(
    basic_modulation_data: dict,
    side_effect: Exception,
    expected_status: int,
    expected_detail: str,
):
    """Database errors during creation should propagate correct responses."""
    mock_session = MagicMock()
    mock_session.commit.side_effect = side_effect

    def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    response = client.post("/modulations/", json=basic_modulation_data)
    assert response.status_code == expected_status
    assert expected_detail in response.json()["detail"]
    app.dependency_overrides.clear()


def test_create_modulation_value_error(basic_modulation_data: dict):
    """Value errors from the model constructor result in client errors."""
    mock_session = MagicMock()

    with patch(
        "app.models.Modulation.__init__",
        side_effect=ValueError("Invalid modulation data"),
    ):

        def override_get_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_get_db
        response = client.post("/modulations/", json=basic_modulation_data)

    assert response.status_code in [400, 422]
    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "side_effect,expected_status,expected_detail",
    [
        (IntegrityError("stmt", "params", "orig"), 409, "already exists"),
        (SQLAlchemyError("db"), 500, "Internal server error"),
    ],
)
def test_update_modulation_db_errors(
    basic_modulation_data: dict,
    side_effect: Exception,
    expected_status: int,
    expected_detail: str,
):
    """Database errors during update should propagate correct responses."""
    mock_modulation = MagicMock()
    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_filter.first.return_value = mock_modulation
    mock_query.filter.return_value = mock_filter
    mock_session.query.return_value = mock_query
    mock_session.commit.side_effect = side_effect

    def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    response = client.put("/modulations/1", json=basic_modulation_data)
    assert response.status_code == expected_status
    assert expected_detail in response.json()["detail"]
    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "patch_factory,expected_status,expected_detail",
    [
        (
            lambda m: _patch_update_setattr_value_error(m, "Invalid modulation data"),
            422,
            "Invalid modulation data",
        ),
    ],
)
def test_update_modulation_value_error(
    basic_modulation_data: dict,
    patch_factory: Callable[[MagicMock], patch],
    expected_status: int,
    expected_detail: str,
):
    """Ensure ValueError paths during modulation update return client errors."""
    mock_modulation = MagicMock()
    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_filter.first.return_value = mock_modulation
    mock_query.filter.return_value = mock_filter
    mock_session.query.return_value = mock_query

    def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    with patch_factory(mock_modulation):
        response = client.put("/modulations/1", json=basic_modulation_data)

    assert response.status_code == expected_status
    assert expected_detail in response.json()["detail"]
    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "method,url",
    [
        ("put", "/modulations/999"),
        ("delete", "/modulations/999"),
    ],
)
def test_modulation_not_found(method: str, url: str, basic_modulation_data: dict):
    """Both update and delete return 404 when the modulation is missing."""
    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_filter.first.return_value = None
    mock_query.filter.return_value = mock_filter
    mock_session.query.return_value = mock_query

    def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    if method == "put":
        response = client.put(url, json=basic_modulation_data)
    else:
        response = client.delete(url)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
    app.dependency_overrides.clear()


def test_delete_modulation_sqlalchemy_error() -> None:
    """SQLAlchemy errors during deletion surface as server errors."""
    mock_modulation = MagicMock()
    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_filter.first.return_value = mock_modulation
    mock_query.filter.return_value = mock_filter
    mock_session.query.return_value = mock_query
    mock_session.commit.side_effect = SQLAlchemyError("db")

    def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    response = client.delete("/modulations/1")
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"
    app.dependency_overrides.clear()
