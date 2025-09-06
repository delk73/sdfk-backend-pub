from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session, selectinload, joinedload
from typing import List
from pydantic import ValidationError
from app.logging import get_logger
from app import models, schemas, security
import app.models.db as db
from app.services import asset_utils

from synesthetic_schemas.synesthetic_asset import SynestheticAsset as ExternalSynestheticAsset
from fastapi.responses import JSONResponse
from app.schema_version import check_schema_header, require_schema_version


def _schema_dep(x_schema_version: str | None = Header(None, alias="X-Schema-Version")):
    check_schema_header(x_schema_version)


router = APIRouter(dependencies=[Depends(_schema_dep)])
logger = get_logger(__name__)


## Removed patch storage helpers (deprecated)


@router.post(
    "/",
    response_model=schemas.SynestheticAssetResponse,
    response_model_exclude_none=True,
)
def create_synesthetic_asset(
    asset: ExternalSynestheticAsset,
    db: Session = Depends(db.get_db),
    token: dict | None = Depends(security.verify_jwt),
    _: None = Depends(require_schema_version),
):
    asset_data = asset.model_dump(mode="json")
    modulations = asset_data.pop("modulations", None)
    meta_info = asset_data.get("meta_info", {})

    modulation_id = None
    if modulations:
        db_mod = models.Modulation(
            name=f"{asset.name} Modulations",
            description=None,
            meta_info={},
            modulations=modulations,
        )
        db.add(db_mod)
        db.commit()
        db.refresh(db_mod)
        modulation_id = db_mod.modulation_id

    asset_data["meta_info"] = meta_info
    if modulation_id is not None:
        asset_data["modulation_id"] = modulation_id

    # Create the asset
    db_asset = models.SynestheticAsset(**asset_data)
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)

    return asset_utils.format_asset_response(db_asset)


@router.post(
    "/nested",
    response_model=schemas.NestedSynestheticAssetResponse,
    response_model_exclude_none=True,
)
def create_nested_synesthetic_asset(
    asset: ExternalSynestheticAsset,
    db: Session = Depends(db.get_db),
    token: dict | None = Depends(security.verify_jwt),
    _: None = Depends(require_schema_version),
):
    """Create a synesthetic asset with nested components"""
    # Create shader if provided
    shader_id = None
    db_shader = None
    if asset.shader:
        shader_data = asset.shader.model_dump(mode="json")
        db_shader = models.Shader(**shader_data)
        db.add(db_shader)
        db.commit()
        db.refresh(db_shader)
        shader_id = db_shader.shader_id

    # Create control if provided
    control_id = None
    db_control = None
    if asset.control:
        control_data = asset.control.model_dump(mode="json")

        # Extract parameters if present
        if "parameters" in control_data:
            control_data.pop("parameters", None)

        # Reuse existing control by name if present (idempotent)
        ctrl_name = control_data.get("name")
        existing_ctrl = None
        if ctrl_name:
            existing_ctrl = (
                db.query(models.Control).filter(models.Control.name == ctrl_name).first()
            )
        if existing_ctrl:
            db_control = existing_ctrl
        else:
            db_control = models.Control(
                name=ctrl_name,
                description=control_data.get("description"),
                meta_info=control_data.get("meta_info", {}),
                control_parameters=control_data.get("control_parameters", []),
            )
            db.add(db_control)
            db.commit()
            db.refresh(db_control)
        control_id = db_control.control_id
    # Handle controls section if present in the asset dict
    elif hasattr(asset, "controls") and asset.controls:
        # Use the controls directly
        controls_list = []
        for control in asset.controls:
            # Create a control entry
            control_entry = {k: v for k, v in control.items()}
            controls_list.append(control_entry)

        if controls_list:
            # Idempotent: reuse control by conventional name if exists
            conventional_name = f"{asset.name} Controls"
            existing_ctrl = (
                db.query(models.Control)
                .filter(models.Control.name == conventional_name)
                .first()
            )
            if existing_ctrl:
                control_id = existing_ctrl.control_id
            else:
                control_obj = models.Control(
                    name=conventional_name,
                    description=f"Controls for {asset.name}",
                    meta_info={
                        "category": "control",
                        "tags": asset.meta_info.get("tags", []) if asset.meta_info else [],
                        "source_asset": asset.name,
                    },
                    control_parameters=controls_list,
                )
                db.add(control_obj)
                db.commit()
                db.refresh(control_obj)
                control_id = control_obj.control_id

    # Create tone if provided
    tone_id = None
    db_tone = None
    if asset.tone:
        tone_data = asset.tone.model_dump(mode="json")

        # Convert Pydantic models to dictionaries for SQLAlchemy
        db_tone_data = {
            "name": tone_data.get("name"),
            "description": tone_data.get("description"),
        }

        # Handle direct fields - convert nested Pydantic models to dictionaries
        if "synth" in tone_data:
            db_tone_data["synth"] = tone_data["synth"]

        if "input_parameters" in tone_data:
            db_tone_data["input_parameters"] = tone_data["input_parameters"]

        if "effects" in tone_data:
            db_tone_data["effects"] = tone_data["effects"]

        if "patterns" in tone_data:
            db_tone_data["patterns"] = tone_data["patterns"]

        if "parts" in tone_data:
            db_tone_data["parts"] = tone_data["parts"]

        if "meta_info" in tone_data:
            db_tone_data["meta_info"] = tone_data["meta_info"]

        db_tone = models.Tone(**db_tone_data)
        db.add(db_tone)
        db.commit()
        db.refresh(db_tone)
        tone_id = db_tone.tone_id

    # Create haptic if provided
    haptic_id = None
    db_haptic = None
    if asset.haptic:
        haptic_data = asset.haptic.model_dump(mode="json")
        db_haptic = models.Haptic(**haptic_data)
        db.add(db_haptic)
        db.commit()
        db.refresh(db_haptic)
        haptic_id = db_haptic.haptic_id

    # Create synesthetic asset
    meta_info = asset.meta_info.copy() if asset.meta_info else {}
    modulation_id = None
    if asset.modulations:
        db_mod = models.Modulation(
            name=f"{asset.name} Modulations",
            description=None,
            meta_info={},
            modulations=asset.modulations,
        )
        db.add(db_mod)
        db.commit()
        db.refresh(db_mod)
        modulation_id = db_mod.modulation_id

    db_asset = models.SynestheticAsset(
        name=asset.name,
        description=asset.description,
        meta_info=meta_info,
        shader_id=shader_id,
        control_id=control_id,
        tone_id=tone_id,
        haptic_id=haptic_id,
        modulation_id=modulation_id,
    )

    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)

    # Format response with components included
    response = asset_utils.format_nested_asset_response(
        db_asset,
        db_shader,
        db_control,
        db_tone,
        db_haptic,
        None,
    )

    # If control_parameters were provided directly in the asset but not through a control object,
    # add them to the response
    if (
        not db_control
        and hasattr(asset, "control_parameters")
        and asset.control_parameters
    ):
        response["control_parameters"] = asset.control_parameters

    return response


from app.schemas.synesthetic_asset_api import PreviewNestedAssetAPI


@router.get("/nested/{asset_id}")
def get_nested_synesthetic_asset(
    asset_id: int,
    db: Session = Depends(db.get_db),
    token: dict | None = Depends(security.verify_jwt),
):
    asset = (
        db.query(models.SynestheticAsset)
        .options(
            joinedload(models.SynestheticAsset.shader),
            joinedload(models.SynestheticAsset.control),
            joinedload(models.SynestheticAsset.tone),
            joinedload(models.SynestheticAsset.haptic),
        )
        .filter(models.SynestheticAsset.synesthetic_asset_id == asset_id)
        .first()
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="Synesthetic asset not found")

    shader = asset.shader
    control = asset.control
    tone = asset.tone
    haptic = asset.haptic
    modulations = asset.modulation.modulations if asset.modulation else None

    response = asset_utils.format_nested_asset_response(
        asset,
        shader,
        control,
        tone,
        haptic,
        modulations,
    )

    # Return stable nested response as JSON to stay permissive
    return JSONResponse(content=jsonable_encoder(response), status_code=200)


@router.get(
    "/{asset_id}",
    response_model=schemas.SynestheticAssetResponse,
    response_model_exclude_none=True,
)
def get_synesthetic_asset(
    asset_id: int,
    db: Session = Depends(db.get_db),
    token: dict | None = Depends(security.verify_jwt),
):
    asset = (
        db.query(models.SynestheticAsset)
        .options(joinedload(models.SynestheticAsset.modulation))
        .filter(models.SynestheticAsset.synesthetic_asset_id == asset_id)
        .first()
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="Synesthetic asset not found")

    modulations = asset.modulation.modulations if asset.modulation else None

    # Create a modified version of the asset with properly structured fields
    response_data = {
        "synesthetic_asset_id": asset.synesthetic_asset_id,
        "name": asset.name,
        "description": asset.description,
        "created_at": asset.created_at,
        "updated_at": asset.updated_at,
    }

    if asset.meta_info:
        meta_info = asset.meta_info.copy()
        meta_info.pop("modulations", None)
        if meta_info:
            response_data["meta_info"] = meta_info

    # If we found modulations, add them to the response
    if modulations:
        response_data["modulations"] = modulations

    # Include component IDs if they exist
    if asset.shader_id:
        response_data["shader_id"] = asset.shader_id
    if asset.control_id:
        response_data["control_id"] = asset.control_id
    if asset.tone_id:
        response_data["tone_id"] = asset.tone_id
    if asset.haptic_id:
        response_data["haptic_id"] = asset.haptic_id

    # Create a Pydantic model for the response
    return schemas.SynestheticAssetResponse(**response_data)


@router.get(
    "/",
    response_model=List[schemas.SynestheticAssetResponse],
    response_model_exclude_none=True,
)
def get_synesthetic_assets(
    db: Session = Depends(db.get_db), token: dict | None = Depends(security.verify_jwt)
):
    assets = (
        db.query(models.SynestheticAsset)
        .options(joinedload(models.SynestheticAsset.modulation))
        .all()
    )

    # Process each asset to ensure modulations are properly extracted
    formatted_assets = []
    for asset in assets:
        modulations = asset.modulation.modulations if asset.modulation else None

        # Create a response with basic asset fields
        response_data = {
            "synesthetic_asset_id": asset.synesthetic_asset_id,
            "name": asset.name,
            "description": asset.description,
            "created_at": asset.created_at,
            "updated_at": asset.updated_at,
        }

        if asset.meta_info:
            meta_info = asset.meta_info.copy()
            meta_info.pop("modulations", None)
            if meta_info:
                response_data["meta_info"] = meta_info

        # Add modulations if they exist
        if modulations:
            response_data["modulations"] = modulations

        # Include component IDs if they exist
        if asset.shader_id:
            response_data["shader_id"] = asset.shader_id
        if asset.control_id:
            response_data["control_id"] = asset.control_id
        if asset.tone_id:
            response_data["tone_id"] = asset.tone_id
        if asset.haptic_id:
            response_data["haptic_id"] = asset.haptic_id

        formatted_assets.append(schemas.SynestheticAssetResponse(**response_data))

    return formatted_assets


@router.get(
    "/offset/",
    response_model=List[schemas.NestedSynestheticAsset],
    response_model_exclude_none=True,
)
def get_synesthetic_assets_offset(
    offset: int = 0,
    limit: int = 10,
    db: Session = Depends(db.get_db),
    token: dict | None = Depends(security.verify_jwt),
):
    """Get synesthetic assets with offset and limit (pagination), nested format, DB only"""
    assets = (
        db.query(models.SynestheticAsset)
        .options(
            selectinload(models.SynestheticAsset.shader),
            selectinload(models.SynestheticAsset.control),
            selectinload(models.SynestheticAsset.tone),
            selectinload(models.SynestheticAsset.haptic),
            selectinload(models.SynestheticAsset.modulation),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    results = []
    for asset in assets:
        modulations = asset.modulation.modulations if asset.modulation else None
        if asset.meta_info:
            meta_info = asset.meta_info.copy()
            meta_info.pop("modulations", None)
        results.append(
            asset_utils.format_nested_asset_response(
                asset,
                asset.shader,
                asset.control,
                asset.tone,
                asset.haptic,
                modulations,
            )
        )
    return results


@router.put(
    "/{asset_id}",
    response_model=schemas.SynestheticAssetResponse,
    response_model_exclude_none=True,
)
def update_synesthetic_asset(
    asset_id: int,
    asset: schemas.SynestheticAssetUpdate,
    db: Session = Depends(db.get_db),
    token: dict | None = Depends(security.verify_jwt),
    _: None = Depends(require_schema_version),
):
    db_asset = (
        db.query(models.SynestheticAsset)
        .filter(models.SynestheticAsset.synesthetic_asset_id == asset_id)
        .first()
    )
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Synesthetic asset not found")

    # Update fields
    update_data = asset.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_asset, key, value)

    db.commit()
    db.refresh(db_asset)
    return asset_utils.format_asset_response(db_asset)


@router.delete(
    "/{asset_id}",
    response_model=schemas.SynestheticAssetResponse,
    response_model_exclude_none=True,
)
def delete_synesthetic_asset(
    asset_id: int,
    db: Session = Depends(db.get_db),
    token: dict | None = Depends(security.verify_jwt),
    _: None = Depends(require_schema_version),
):
    db_asset = (
        db.query(models.SynestheticAsset)
        .filter(models.SynestheticAsset.synesthetic_asset_id == asset_id)
        .first()
    )
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Synesthetic asset not found")

    # Save response before deletion
    response = asset_utils.format_asset_response(db_asset)

    db.delete(db_asset)
    db.commit()
    return response


@router.put(
    "/{asset_id}/shader",
    response_model=schemas.NestedSynestheticAssetResponse,
    response_model_exclude_none=True,
)
def update_asset_shader(
    asset_id: int,
    shader_update: schemas.ShaderUpdate,
    db: Session = Depends(db.get_db),
    token: dict | None = Depends(security.verify_jwt),
    _: None = Depends(require_schema_version),
):
    """Update the shader component for a synesthetic asset."""
    db_asset = (
        db.query(models.SynestheticAsset)
        .filter(models.SynestheticAsset.synesthetic_asset_id == asset_id)
        .first()
    )
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Synesthetic asset not found")
    if not db_asset.shader_id:
        raise HTTPException(status_code=404, detail="Shader not found for asset")

    db_shader = (
        db.query(models.Shader)
        .filter(models.Shader.shader_id == db_asset.shader_id)
        .first()
    )
    if db_shader is None:
        raise HTTPException(status_code=404, detail="Shader not found")

    for key, value in shader_update.model_dump(exclude_unset=True).items():
        setattr(db_shader, key, value)
    db.commit()
    db.refresh(db_shader)

    return get_nested_synesthetic_asset(asset_id, db=db, token=None)


@router.put(
    "/{asset_id}/tone",
    response_model=schemas.NestedSynestheticAssetResponse,
    response_model_exclude_none=True,
)
def update_asset_tone(
    asset_id: int,
    tone_update: schemas.ToneUpdate,
    db: Session = Depends(db.get_db),
    token: dict | None = Depends(security.verify_jwt),
    _: None = Depends(require_schema_version),
):
    """Update the tone component for a synesthetic asset."""
    db_asset = (
        db.query(models.SynestheticAsset)
        .filter(models.SynestheticAsset.synesthetic_asset_id == asset_id)
        .first()
    )
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Synesthetic asset not found")
    if not db_asset.tone_id:
        raise HTTPException(status_code=404, detail="Tone not found for asset")

    db_tone = (
        db.query(models.Tone).filter(models.Tone.tone_id == db_asset.tone_id).first()
    )
    if db_tone is None:
        raise HTTPException(status_code=404, detail="Tone not found")

    for key, value in tone_update.model_dump(exclude_unset=True).items():
        setattr(db_tone, key, value)
    db.commit()
    db.refresh(db_tone)

    return get_nested_synesthetic_asset(asset_id, db=db, token=None)


@router.put(
    "/{asset_id}/haptic",
    response_model=schemas.NestedSynestheticAssetResponse,
    response_model_exclude_none=True,
)
def update_asset_haptic(
    asset_id: int,
    haptic_update: schemas.HapticUpdate,
    db: Session = Depends(db.get_db),
    token: dict | None = Depends(security.verify_jwt),
    _: None = Depends(require_schema_version),
):
    """Update the haptic component for a synesthetic asset."""
    db_asset = (
        db.query(models.SynestheticAsset)
        .filter(models.SynestheticAsset.synesthetic_asset_id == asset_id)
        .first()
    )
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Synesthetic asset not found")
    if not db_asset.haptic_id:
        raise HTTPException(status_code=404, detail="Haptic not found for asset")

    db_haptic = (
        db.query(models.Haptic)
        .filter(models.Haptic.haptic_id == db_asset.haptic_id)
        .first()
    )
    if db_haptic is None:
        raise HTTPException(status_code=404, detail="Haptic not found")

    for key, value in haptic_update.model_dump(exclude_unset=True).items():
        setattr(db_haptic, key, value)
    db.commit()
    db.refresh(db_haptic)

    return get_nested_synesthetic_asset(asset_id, db=db, token=None)


## Patch preview/apply routes removed (repository now serves CRUD only)
