from __future__ import annotations

"""Utility for generating standard CRUD routers."""

from typing import Type, TypeVar, List, Optional, Any, cast
from fastapi import APIRouter, Depends, HTTPException, Body, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, Mapper
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import security
from app.models.db import get_db
from app.schema_version import require_schema_version

ModelT = TypeVar("ModelT")
CreateSchemaT = TypeVar("CreateSchemaT", bound=BaseModel)
UpdateSchemaT = TypeVar("UpdateSchemaT", bound=BaseModel)
ResponseSchemaT = TypeVar("ResponseSchemaT", bound=BaseModel)


def create_crud_router(
    model: Type[ModelT],
    create_schema: Type[CreateSchemaT],
    update_schema: Type[UpdateSchemaT],
    response_schema: Type[ResponseSchemaT],
    *,
    router_kwargs: Optional[dict] = None,
) -> APIRouter:
    """Return an APIRouter with basic CRUD routes for ``model``.

    Args:
        model: SQLAlchemy model class.
        create_schema: Pydantic schema used for ``POST`` requests.
        update_schema: Pydantic schema used for ``PUT`` requests.
        response_schema: Schema returned in responses.
        router_kwargs: Optional arguments passed to :class:`APIRouter`.
    """
    router = APIRouter(**(router_kwargs or {}))
    mapper = cast("Mapper[Any]", inspect(model))
    pk_name = mapper.primary_key[0].name
    pk_attr = getattr(model, pk_name)

    def _normalize_for_response(model_name: str, data: dict) -> dict:
        """Ensure list-typed fields are lists instead of None for known models."""
        if model_name == "Tone":
            for key in ("input_parameters", "effects", "patterns", "parts"):
                if data.get(key) is None:
                    data[key] = []
        if model_name == "Haptic":
            if data.get("input_parameters") is None:
                data["input_parameters"] = []
        if model_name == "Modulation":
            if data.get("modulations") is None:
                data["modulations"] = []
        return data

    @router.post("/", response_model=response_schema)
    def create_item(
        payload: CreateSchemaT = Body(...),
        db: Session = Depends(get_db),
        token: dict | None = Depends(security.verify_jwt),
        _: None = Depends(require_schema_version),
    ) -> ModelT | dict[str, Any]:
        try:
            # Ensure JSON-safe (no Enums/Pydantic objects) for JSON columns
            data = payload.model_dump(mode="json")
            # Normalize control bundle structures to avoid None/null pitfalls
            if getattr(model, "__name__", "") == "Control":
                params = data.get("control_parameters")
                if isinstance(params, list):
                    for p in params:
                        mappings = p.get("mappings")
                        if isinstance(mappings, list):
                            for m in mappings:
                                combo = m.get("combo")
                                if isinstance(combo, dict):
                                    combo.setdefault("wheel", False)
                                    combo.setdefault("keys", [])
                                    combo.setdefault("mouseButtons", [])
            instance = model(**data)
            db.add(instance)
            db.commit()
            db.refresh(instance)
            # For Control, format response explicitly to avoid validation drift
            if getattr(model, "__name__", "") == "Control":
                try:
                    from app.services.asset_utils import format_control_response

                    resp = format_control_response(instance) or {}
                    resp["control_id"] = instance.control_id
                    shaped = response_schema.model_validate(resp)
                    return shaped.model_dump()
                except Exception:
                    pass
            result = getattr(instance, "to_dict", lambda: instance)()
            if isinstance(result, dict):
                result = _normalize_for_response(getattr(model, "__name__", ""), result)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{model.__name__} with this name already exists",
            )
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )
        # Shape the response to match the declared schema
        try:
            shaped = response_schema.model_validate(result)
            return shaped.model_dump()
        except Exception:
            # Fall back to raw result if validation fails; FastAPI will re-validate
            return result

    # Update annotation after function definition to avoid ForwardRef issues
    create_item.__annotations__["payload"] = create_schema

    @router.get("/{item_id}", response_model=response_schema)
    def read_item(
        item_id: int,
        db: Session = Depends(get_db),
        token: dict | None = Depends(security.verify_jwt),
    ) -> ModelT | dict[str, Any]:
        instance = db.query(model).filter(pk_attr == item_id).first()
        if instance is None:
            raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
        try:
            result = getattr(instance, "to_dict", lambda: instance)()
            if isinstance(result, dict):
                result = _normalize_for_response(getattr(model, "__name__", ""), result)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            )
        try:
            shaped = response_schema.model_validate(result)
            return shaped.model_dump()
        except Exception:
            return result

    response_list_model = cast(Any, List)[response_schema]

    @router.get("/", response_model=response_list_model)
    def read_items(
        db: Session = Depends(get_db),
        token: dict | None = Depends(security.verify_jwt),
    ) -> List[ModelT | dict[str, Any]]:
        instances = db.query(model).all()
        items: List[ModelT | dict[str, Any]] = []
        for inst in instances:
            try:
                item = getattr(inst, "to_dict", lambda: inst)()
                if isinstance(item, dict):
                    item = _normalize_for_response(getattr(model, "__name__", ""), item)
                items.append(item)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=str(exc),
                )
        try:
            shaped_list = [response_schema.model_validate(i).model_dump() for i in items]
            return shaped_list
        except Exception:
            return items

    @router.put("/{item_id}", response_model=response_schema)
    def update_item(
        item_id: int,
        payload: UpdateSchemaT = Body(...),
        db: Session = Depends(get_db),
        token: dict | None = Depends(security.verify_jwt),
        _: None = Depends(require_schema_version),
    ) -> ModelT | dict[str, Any]:
        instance = db.query(model).filter(pk_attr == item_id).first()
        if instance is None:
            raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
        try:
            # Ensure JSON-safe (no Enums/Pydantic objects) for JSON columns
            for key, value in payload.model_dump(mode="json", exclude_unset=True).items():
                setattr(instance, key, value)
            db.commit()
            db.refresh(instance)
            result = getattr(instance, "to_dict", lambda: instance)()
            if isinstance(result, dict):
                result = _normalize_for_response(getattr(model, "__name__", ""), result)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{model.__name__} with this name already exists",
            )
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )
        try:
            shaped = response_schema.model_validate(result)
            return shaped.model_dump()
        except Exception:
            return result

    update_item.__annotations__["payload"] = update_schema

    @router.delete("/{item_id}", response_model=response_schema)
    def delete_item(
        item_id: int,
        db: Session = Depends(get_db),
        token: dict | None = Depends(security.verify_jwt),
        _: None = Depends(require_schema_version),
    ) -> ModelT | dict[str, Any]:
        instance = db.query(model).filter(pk_attr == item_id).first()
        if instance is None:
            raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
        try:
            result = getattr(instance, "to_dict", lambda: instance)()
            if isinstance(result, dict):
                result = _normalize_for_response(getattr(model, "__name__", ""), result)
            db.delete(instance)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            )
        try:
            shaped = response_schema.model_validate(result)
            return shaped.model_dump()
        except Exception:
            return result

    return router
