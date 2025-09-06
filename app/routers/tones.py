from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from typing import List, Dict, Any
from pydantic import ValidationError
from app import models, schemas, security
from synesthetic_schemas.tone import SynthType
from app.schema_version import require_schema_version
from synesthetic_schemas.tone import Tone as ToneCreateSchema
import app.models.db as db
from app.logging import get_logger
from app.services import asset_utils

router = APIRouter()
logger = get_logger(__name__)

_ALLOWED_FIELDS = {c.key for c in inspect(models.Tone).mapper.column_attrs}


def _filter_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return a dict containing only keys valid for :class:`Tone`."""
    return {k: v for k, v in data.items() if k in _ALLOWED_FIELDS}


def tone_to_response(db_tone: models.Tone) -> dict:
    """Return serialized tone with ``tone_id`` field included.

    Raises:
        ValueError: If ``db_tone`` is ``None`` or cannot be serialized.
    """

    if db_tone is None:
        raise ValueError("db_tone must not be None")

    response = asset_utils.format_tone_response(db_tone)
    if response is None:
        raise ValueError("Failed to serialize tone")

    response["tone_id"] = db_tone.tone_id
    return response


def apply_update(db_tone: models.Tone, payload: schemas.ToneUpdate) -> None:
    """Apply a ``ToneUpdate`` payload to a :class:`models.Tone`."""
    for key, value in _filter_fields(payload.model_dump(exclude_unset=True)).items():
        setattr(db_tone, key, value)


@router.post("/", response_model=schemas.Tone, status_code=status.HTTP_200_OK)
async def create_tone(
    tone_create: ToneCreateSchema,
    db: Session = Depends(db.get_db),
    token: dict | None = Depends(security.verify_jwt),
    _: None = Depends(require_schema_version),
):
    # Enforce synth type enum (bring back strictness for API requests)
    try:
        allowed = {st.value for st in SynthType}
        synth_type = None
        if isinstance(tone_create.synth, dict):
            synth_type = tone_create.synth.get("type")
        elif hasattr(tone_create.synth, "type"):
            synth_type = tone_create.synth.type
        if synth_type not in allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid synth type: {synth_type}",
            )
    except AttributeError:
        # Missing synth handled by FastAPI validation elsewhere
        pass
    try:
        db_tone = models.Tone(**_filter_fields(tone_create.model_dump()))
        db.add(db_tone)
        db.commit()
        db.refresh(db_tone)
        return tone_to_response(db_tone)
    except Exception as e:  # pragma: no cover - unexpected DB errors
        logger.error(f"Error creating tone: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/{tone_id}", response_model=schemas.Tone)
def get_tone(
    tone_id: int,
    db: Session = Depends(db.get_db),
    token: dict | None = Depends(security.verify_jwt),
):
    db_tone = db.query(models.Tone).filter(models.Tone.tone_id == tone_id).first()
    if db_tone is None:
        raise HTTPException(status_code=404, detail="Tone not found")

    return tone_to_response(db_tone)


@router.get("/", response_model=List[schemas.Tone])
def get_tones(
    db: Session = Depends(db.get_db),
    token: dict | None = Depends(security.verify_jwt),
):
    db_tones = db.query(models.Tone).all()
    responses: List[Dict[str, Any]] = []
    for tone in db_tones:
        try:
            tone_dict = tone_to_response(tone)
        except (ValueError, ValidationError) as exc:
            logger.error(
                "Error processing tone %s: %s",
                getattr(tone, "tone_id", "unknown"),
                exc,
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )
        responses.append(tone_dict)
    return responses


@router.put("/{tone_id}", response_model=schemas.Tone)
async def update_tone(
    tone_id: int,
    tone_update: schemas.ToneUpdate,
    db: Session = Depends(db.get_db),
    token: dict | None = Depends(security.verify_jwt),
    _: None = Depends(require_schema_version),
):
    db_tone = db.query(models.Tone).filter(models.Tone.tone_id == tone_id).first()
    if not db_tone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tone with ID {tone_id} not found",
        )

    try:
        # Enforce synth type on update when provided
        if tone_update.synth is not None:
            allowed = {st.value for st in SynthType}
            synth_type = None
            if isinstance(tone_update.synth, dict):
                synth_type = tone_update.synth.get("type")
            elif hasattr(tone_update.synth, "type"):
                synth_type = tone_update.synth.type
            if synth_type not in allowed:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid synth type: {synth_type}",
                )
        apply_update(db_tone, tone_update)
        db.commit()
        db.refresh(db_tone)
        return tone_to_response(db_tone)
    except Exception as e:  # pragma: no cover - unexpected DB errors
        logger.error(f"Error updating tone: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.delete("/{tone_id}", response_model=schemas.Tone)
def delete_tone(
    tone_id: int,
    db: Session = Depends(db.get_db),
    token: dict | None = Depends(security.verify_jwt),
):
    db_tone = db.query(models.Tone).filter(models.Tone.tone_id == tone_id).first()
    if db_tone is None:
        raise HTTPException(status_code=404, detail="Tone not found")

    # Save response before deletion
    response = tone_to_response(db_tone)

    db.delete(db_tone)
    db.commit()

    return response
