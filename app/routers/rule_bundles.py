"""CRUD routes for rule bundle management using external schemas."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.models.db import get_db
from app import models
from synesthetic_schemas.rule_bundle import RuleBundle as RuleBundleSchema
from app.schema_version import require_schema_version

router = APIRouter()


@router.post("/", response_model=RuleBundleSchema)
def create_bundle(
    bundle: RuleBundleSchema,
    db: Session = Depends(get_db),
    _: None = Depends(require_schema_version),
):
    """Create a new rule bundle."""
    obj = models.RuleBundle(**bundle.model_dump(exclude_unset=True))
    db.add(obj)
    db.commit()
    db.refresh(obj)
    # Validate and shape response via external schema
    return RuleBundleSchema.model_validate(obj).model_dump()


@router.get("/{bundle_id}", response_model=RuleBundleSchema)
def get_bundle(
    bundle_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve a rule bundle by ID."""
    obj = db.query(models.RuleBundle).get(bundle_id)
    if not obj:
        raise HTTPException(status_code=404, detail="RuleBundle not found")
    return RuleBundleSchema.model_validate(obj).model_dump()


@router.post("/import", response_model=RuleBundleSchema)
def import_bundle(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: None = Depends(require_schema_version),
):
    """Import a rule bundle from an uploaded JSON file."""
    data = json.load(file.file)
    schema = RuleBundleSchema(**data)
    return create_bundle(schema, db)
