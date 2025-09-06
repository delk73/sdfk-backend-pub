"""Coverage tests for the controls router focusing on error handling paths."""

from __future__ import annotations

import builtins
from contextlib import ExitStack
from typing import Callable, Iterable, Tuple
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import security
from app.main import app
from app.models.db import get_db

# Override JWT verification for tests
app.dependency_overrides[security.verify_jwt] = lambda token=None: {"sub": "test_user"}

client = TestClient(app)


@pytest.fixture
def basic_control_data() -> dict:
    """Return basic control payload used by multiple tests."""
    return {
        "name": "Test Control",
        "description": "Test control description",
        "meta_info": {"category": "test", "tags": ["test", "coverage"]},
        "control_parameters": [
            {
                "parameter": "visual.param1",
                "label": "Parameter 1",
                "type": "float",
                "unit": "linear",
                "default": 0.0,
                "min": 0.0,
                "max": 1.0,
                "step": 0.01,
                "smoothingTime": 0.1,
                "mappings": [
                    {
                        "combo": {"mouseButtons": ["left"], "strict": True},
                        "action": {
                            "axis": "mouse.x",
                            "sensitivity": 0.01,
                            "scale": 1.0,
                            "curve": "linear",
                        },
                    }
                ],
            }
        ],
    }


def _patch_model_dump_value_error(message: str) -> patch:
    return patch("pydantic.main.BaseModel.model_dump", side_effect=ValueError(message))


def _patch_control_init_value_error(message: str) -> patch:
    return patch("app.models.Control.__init__", side_effect=ValueError(message))


def _patch_control_constructor_value_error(message: str) -> patch:
    return patch("app.models.Control.__init__", side_effect=ValueError(message))


def _patch_control_to_dict_value_error(message: str) -> patch:
    return patch("app.models.control.Control.to_dict", side_effect=ValueError(message))


def _patch_update_setattr_value_error(mock_control: MagicMock, message: str) -> patch:
    original_setattr = builtins.setattr

    def mocked(obj, name, value):
        if obj is mock_control and name == "name":
            raise ValueError(message)
        return original_setattr(obj, name, value)

    return patch("builtins.setattr", mocked)


def _patch_update_to_dict_value_error(mock_control: MagicMock, message: str) -> patch:
    return patch.object(mock_control, "to_dict", side_effect=ValueError(message))


@pytest.mark.parametrize(
    "patch_factories",
    [
        [lambda: _patch_model_dump_value_error("Invalid control data")],
        [lambda: _patch_control_to_dict_value_error("Specific validation error")],
        [lambda: _patch_control_init_value_error("Direct validation error")],
        [
            lambda: _patch_control_constructor_value_error(
                "At least one control parameter is required"
            )
        ],
        [lambda: _patch_control_constructor_value_error("Targeted validation error")],
        [lambda: _patch_control_to_dict_value_error("Final validation error")],
    ],
)
def test_create_control_value_errors(
    basic_control_data: dict,
    patch_factories: Iterable[Callable[[], patch | Tuple[patch, ...]]],
):
    """Ensure various ValueError paths during control creation return 4xx codes."""
    mock_session = MagicMock()

    def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    with ExitStack() as stack:
        for factory in patch_factories:
            obj = factory()
            if isinstance(obj, tuple):
                for p_obj in obj:
                    stack.enter_context(p_obj)
            else:
                stack.enter_context(obj)
        response = client.post("/controls/", json=basic_control_data)

    assert response.status_code in [400, 422]
    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "side_effect,expected_status,expected_detail",
    [
        (IntegrityError("stmt", "params", "orig"), 409, "already exists"),
        (SQLAlchemyError("db"), 500, "Internal server error"),
    ],
)
def test_create_control_db_errors(
    basic_control_data: dict,
    side_effect: Exception,
    expected_status: int,
    expected_detail: str,
):
    """Database errors during creation should propagate proper responses."""
    mock_session = MagicMock()
    mock_session.commit.side_effect = side_effect

    def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    response = client.post("/controls/", json=basic_control_data)
    assert response.status_code == expected_status
    assert expected_detail in response.json()["detail"]
    app.dependency_overrides.clear()


def test_update_nonexistent_control(basic_control_data: dict):
    """Updating a missing control yields a 404 response."""
    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_filter.first.return_value = None
    mock_query.filter.return_value = mock_filter
    mock_session.query.return_value = mock_query

    def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    response = client.put("/controls/999", json=basic_control_data)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "side_effect,expected_status,expected_detail",
    [
        (IntegrityError("stmt", "params", "orig"), 409, "already exists"),
        (SQLAlchemyError("db"), 500, "Internal server error"),
    ],
)
def test_update_control_db_errors(
    basic_control_data: dict,
    side_effect: Exception,
    expected_status: int,
    expected_detail: str,
):
    """Database errors during update should propagate proper responses."""
    mock_control = MagicMock()
    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_filter.first.return_value = mock_control
    mock_query.filter.return_value = mock_filter
    mock_session.query.return_value = mock_query
    mock_session.commit.side_effect = side_effect

    def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    response = client.put("/controls/1", json=basic_control_data)
    assert response.status_code == expected_status
    assert expected_detail in response.json()["detail"]
    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "patch_factory,expected_statuses,expected_detail",
    [
        (
            lambda mc: _patch_update_setattr_value_error(mc, "Invalid control data"),
            [422],
            "Invalid control data",
        ),
        (
            lambda mc: _patch_update_setattr_value_error(
                mc, "Targeted update validation error"
            ),
            [400, 422],
            None,
        ),
        (
            lambda mc: _patch_update_to_dict_value_error(
                mc, "Final update validation error"
            ),
            [422],
            "Final update validation error",
        ),
    ],
)
def test_update_control_value_errors(
    basic_control_data: dict,
    patch_factory: Callable[[MagicMock], patch],
    expected_statuses: Iterable[int],
    expected_detail: str | None,
):
    """Ensure various ValueError paths during control update return 4xx codes."""
    mock_control = MagicMock()
    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_filter.first.return_value = mock_control
    mock_query.filter.return_value = mock_filter
    mock_session.query.return_value = mock_query

    def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    with patch_factory(mock_control):
        response = client.put("/controls/1", json=basic_control_data)

    assert response.status_code in expected_statuses
    if expected_detail:
        assert expected_detail in response.json()["detail"]
    app.dependency_overrides.clear()


def test_delete_nonexistent_control() -> None:
    """Deleting a missing control returns 404."""
    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_filter.first.return_value = None
    mock_query.filter.return_value = mock_filter
    mock_session.query.return_value = mock_query

    def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    response = client.delete("/controls/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
    app.dependency_overrides.clear()


def test_delete_control_sqlalchemy_error() -> None:
    """SQLAlchemy errors during deletion surface as server errors."""
    mock_control = MagicMock()
    mock_control.to_dict.return_value = {
        "control_id": 1,
        "name": "Test Control",
        "description": "Test",
        "meta_info": {"category": "test"},
        "control_parameters": [],
    }
    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_filter.first.return_value = mock_control
    mock_query.filter.return_value = mock_filter
    mock_session.query.return_value = mock_query
    mock_session.commit.side_effect = SQLAlchemyError("db")

    def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    response = client.delete("/controls/1")
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"
    app.dependency_overrides.clear()
