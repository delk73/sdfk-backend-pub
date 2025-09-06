"""CRUD routes for Shader using external schema with formatted responses."""

from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session

from app import security
from app.models.db import get_db
from app import models
from app.services import asset_utils
from synesthetic_schemas.shader import Shader as ShaderSchema
from app.schemas import ShaderUpdate
from app.schemas.shader_api import ShaderAPIResponse
from app.schema_version import require_schema_version


router = APIRouter(
    tags=["shaders"], dependencies=[Depends(security.verify_jwt)]
)


@router.post("/", response_model=ShaderAPIResponse)
def create_shader(
    payload: ShaderSchema = Body(...),
    db: Session = Depends(get_db),
    _: None = Depends(require_schema_version),
):
    try:
        instance = models.Shader(**payload.model_dump())
        db.add(instance)
        db.commit()
        db.refresh(instance)
        result = asset_utils.format_shader_response(instance)
        if result is None:
            raise ValueError("Failed to serialize shader")
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get("/{shader_id}", response_model=ShaderAPIResponse)
def get_shader(
    shader_id: int,
    db: Session = Depends(get_db),
):
    instance = db.query(models.Shader).filter(models.Shader.shader_id == shader_id).first()
    if instance is None:
        raise HTTPException(status_code=404, detail="Shader not found")
    result = asset_utils.format_shader_response(instance)
    if result is None:
        raise HTTPException(status_code=500, detail="Internal server error")
    return result


@router.get("/", response_model=list[ShaderAPIResponse])
def list_shaders(
    db: Session = Depends(get_db),
):
    instances = db.query(models.Shader).all()
    items = []
    for inst in instances:
        res = asset_utils.format_shader_response(inst)
        if res is None:
            raise HTTPException(status_code=500, detail="Internal server error")
        items.append(res)
    return items


@router.put("/{shader_id}", response_model=ShaderAPIResponse)
def update_shader(
    shader_id: int,
    payload: ShaderUpdate = Body(...),
    db: Session = Depends(get_db),
    _: None = Depends(require_schema_version),
):
    instance = db.query(models.Shader).filter(models.Shader.shader_id == shader_id).first()
    if instance is None:
        raise HTTPException(status_code=404, detail="Shader not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, key, value)
    db.commit()
    db.refresh(instance)
    res = asset_utils.format_shader_response(instance)
    if res is None:
        raise HTTPException(status_code=500, detail="Internal server error")
    return res


@router.delete("/{shader_id}", response_model=ShaderAPIResponse)
def delete_shader(
    shader_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_schema_version),
):
    instance = db.query(models.Shader).filter(models.Shader.shader_id == shader_id).first()
    if instance is None:
        raise HTTPException(status_code=404, detail="Shader not found")
    res = asset_utils.format_shader_response(instance)
    if res is None:
        raise HTTPException(status_code=500, detail="Internal server error")
    db.delete(instance)
    db.commit()
    return res


__all__ = ["router"]
