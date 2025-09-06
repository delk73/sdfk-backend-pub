"""CRUD routes for :class:`Control` using the generic router factory."""

from fastapi import Depends

from app.models.db import get_db

from app import security
from app.models import Control
from app.schemas.control_api import ControlAPIResponse
from synesthetic_schemas.control_bundle import ControlBundle as ControlCreate
from app.utils.crud_router import create_crud_router


router = create_crud_router(
    Control,
    ControlCreate,
    ControlCreate,
    ControlAPIResponse,
    router_kwargs={
        "tags": ["controls"],
        "dependencies": [Depends(security.verify_jwt)],
    },
)

__all__ = ["router", "get_db"]
