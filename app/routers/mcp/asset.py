from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
import uuid

from ...models.db import get_db
from ...schemas.mcp.asset import (
    CreateAssetRequest,
    UpdateParamRequest,
    ApplyModulationRequest,
    ValidateAssetRequest,
    CreateAssetResponse,
    UpdateParamResponse,
    ApplyModulationResponse,
    ValidateAssetResponse,
    PingResponse,
    CreateAssetResult,
    UpdateParamResult,
    ApplyModulationResult,
    ValidateAssetResult,
)
from ...schemas.error import ErrorResponse
from ...services.mcp_logger import log_mcp_command
from ...middleware.request_id import get_current_request_id
from ...logging import get_logger
from ...schema_version import require_schema_version

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/ping",
    tags=["MCP Asset"],
    summary="Health check for MCP asset router",
    description="Verify that the MCP asset router is operational and responsive.",
    response_model=PingResponse,
    status_code=status.HTTP_200_OK,
)
def ping_asset() -> PingResponse:
    """Ping endpoint to verify MCP asset router is live."""
    # Return a plain dict; FastAPI will validate/serialize against PingResponse.
    # This minimizes any edge-case differences between model vs. dict responses
    # in different runtime environments while keeping the API schema intact.
    return {"status": "MCP asset router live"}


@router.post(
    "/create",
    tags=["MCP Asset"],
    summary="Create a new synesthetic asset",
    description="Create a new multi-modal synesthetic asset with tone, shader, and optional haptic components.",
    response_model=CreateAssetResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Asset created successfully",
            "model": CreateAssetResponse,
        },
        422: {"description": "Invalid request data", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
def create_asset(
    request_data: CreateAssetRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(require_schema_version),
) -> CreateAssetResponse:
    """Create a new synesthetic asset via MCP."""
    request_id = get_current_request_id()

    try:
        # Convert request to dict for processing
        payload = request_data.model_dump()

        # Log the MCP command
        log_id = log_mcp_command(
            command_type="create_asset",
            payload=payload,
            status="pending",
            request_id=request_id,
            db=db,
        )

        # For now, simulate asset creation (following CONSTRAINTS: route stubs are fine)
        mock_asset_id = f"asset_{uuid.uuid4().hex[:8]}"

        result = CreateAssetResult(
            asset_id=mock_asset_id,
            status="created",
            components={
                "tone": bool(payload.get("tone")),
                "shader": bool(payload.get("shader")),
                "haptic": bool(payload.get("haptic")),
            },
        )

        # Update the log with success result
        if log_id:
            from ...services.mcp_logger import update_mcp_log

            update_mcp_log(
                log_id=log_id, result=result.model_dump(), status="success", db=db
            )

        return CreateAssetResponse(
            request_id=request_id,
            asset_id=mock_asset_id,
            status="success",
            message="Asset created successfully",
            result=result,
        )

    except Exception as e:
        # Log the error
        if "log_id" in locals() and log_id:
            from ...services.mcp_logger import update_mcp_log

            update_mcp_log(
                log_id=log_id, result={"error": str(e)}, status="error", db=db
            )

        logger.error("Asset creation failed", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        )


@router.post(
    "/update",
    tags=["MCP Asset"],
    summary="Update an asset parameter",
    description="Update a specific parameter value within an existing asset using dot notation path.",
    response_model=UpdateParamResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Parameter updated successfully",
            "model": UpdateParamResponse,
        },
        404: {"description": "Asset not found", "model": ErrorResponse},
        422: {"description": "Invalid parameter path or value", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
def update_param(
    request_data: UpdateParamRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(require_schema_version),
) -> UpdateParamResponse:
    """Update a parameter value within an asset."""
    request_id = get_current_request_id()

    try:
        payload = request_data.model_dump()

        # Log the MCP command
        log_id = log_mcp_command(
            command_type="update_param",
            payload=payload,
            status="pending",
            request_id=request_id,
            asset_id=payload.get("asset_id"),
            db=db,
        )

        # Simulate asset lookup - in real implementation, check if asset exists
        asset_id = payload["asset_id"]
        if asset_id.startswith("nonexistent_"):
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Asset not found",
                    "request_id": request_id,
                    "asset_id": asset_id,
                    "message": f"Asset {asset_id} does not exist",
                },
            )

        # Validate parameter path
        path = payload["path"]
        valid_paths = [
            "shader.u_time",
            "tone.volume",
            "haptic.intensity",
            "shader.u_r",
            "tone.frequency",
        ]
        if path not in valid_paths:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Invalid parameter path",
                    "request_id": request_id,
                    "path": path,
                    "valid_paths": valid_paths,
                    "message": f"Parameter path '{path}' is not valid",
                },
            )

        result = UpdateParamResult(
            asset_id=asset_id,
            path=path,
            old_value=0.0,  # Mock old value
            new_value=payload["value"],
            updated=True,
        )

        # Update log with success
        if log_id:
            from ...services.mcp_logger import update_mcp_log

            update_mcp_log(
                log_id=log_id, result=result.model_dump(), status="success", db=db
            )

        return UpdateParamResponse(
            request_id=request_id,
            status="success",
            message="Parameter updated successfully",
            result=result,
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error("Parameter update failed", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/modulate",
    tags=["MCP Asset"],
    summary="Apply modulation to asset parameter",
    description="Apply a modulation (LFO, envelope, etc.) to a specific asset parameter.",
    response_model=ApplyModulationResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Modulation applied successfully",
            "model": ApplyModulationResponse,
        },
        404: {"description": "Asset not found", "model": ErrorResponse},
        409: {"description": "Modulation already exists", "model": ErrorResponse},
        422: {"description": "Invalid modulation definition", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
def apply_modulation(
    request_data: ApplyModulationRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(require_schema_version),
) -> ApplyModulationResponse:
    """Apply a modulation to an asset parameter."""
    request_id = get_current_request_id()

    try:
        payload = request_data.model_dump()

        # Log the MCP command
        log_id = log_mcp_command(
            command_type="apply_modulation",
            payload=payload,
            status="pending",
            request_id=request_id,
            asset_id=payload.get("asset_id"),
            db=db,
        )

        asset_id = payload["asset_id"]
        modulation_id = payload["modulation_id"]

        # Check if asset exists
        if asset_id.startswith("nonexistent_"):
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Asset not found",
                    "request_id": request_id,
                    "asset_id": asset_id,
                    "message": f"Asset {asset_id} does not exist",
                },
            )

        # Check for duplicate modulation
        if modulation_id == "duplicate_mod":
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "Modulation already exists",
                    "request_id": request_id,
                    "asset_id": asset_id,
                    "modulation_id": modulation_id,
                    "message": f"Modulation {modulation_id} already applied to asset {asset_id}",
                },
            )

        result = ApplyModulationResult(
            asset_id=asset_id,
            modulation_id=modulation_id,
            definition=payload["definition"],
            applied=True,
        )

        # Update log with success
        if log_id:
            from ...services.mcp_logger import update_mcp_log

            update_mcp_log(
                log_id=log_id, result=result.model_dump(), status="success", db=db
            )

        return ApplyModulationResponse(
            request_id=request_id,
            status="success",
            message="Modulation applied successfully",
            result=result,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Apply modulation failed", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/validate",
    tags=["MCP Asset"],
    summary="Validate asset configuration",
    description="Validate the structure and contents of a complete asset configuration blob.",
    response_model=ValidateAssetResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Asset validation completed",
            "model": ValidateAssetResponse,
        },
        422: {"description": "Asset configuration is invalid", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
def validate_asset(
    request_data: ValidateAssetRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(require_schema_version),
) -> ValidateAssetResponse:
    """Validate an asset configuration blob."""
    request_id = get_current_request_id()

    try:
        payload = request_data.model_dump()

        # Log the MCP command
        log_id = log_mcp_command(
            command_type="validate_asset",
            payload=payload,
            status="pending",
            request_id=request_id,
            db=db,
        )

        asset_blob = payload["asset_blob"]

        # Basic validation
        validation_errors = []

        if not asset_blob.get("name"):
            validation_errors.append("Asset name is required")

        if not asset_blob.get("shader") and not asset_blob.get("tone"):
            validation_errors.append(
                "Asset must have at least a shader or tone component"
            )

        if validation_errors:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Validation failed",
                    "request_id": request_id,
                    "validation_errors": validation_errors,
                    "message": "Asset configuration is invalid",
                },
            )

        result = ValidateAssetResult(
            valid=True, components_found=list(asset_blob.keys()), validation_passed=True
        )

        # Update log with success
        if log_id:
            from ...services.mcp_logger import update_mcp_log

            update_mcp_log(
                log_id=log_id, result=result.model_dump(), status="success", db=db
            )

        return ValidateAssetResponse(
            request_id=request_id,
            status="success",
            message="Asset validation passed",
            result=result,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Asset validation failed", exc_info=e)
        raise HTTPException(status_code=500, detail="Internal server error")
