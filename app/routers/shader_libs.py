"""Routes for shader library utilities."""

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from .factory import shader_lib_router as router
from app.models.db import get_db
from app.models.shader_lib import ShaderLib as ShaderLibModel
from app.security import require_auth
from app.shaderlib import (
    ShaderLib as ShaderLibSchema,
    collect_effective_inputs,
    check_template_demonstrates_helper,
    verror,
)

router.dependencies.append(Depends(require_auth))


@router.get(
    "/{id}/helpers/{name}/effective",
    responses={
        200: {
            "description": "Merged uniforms and input parameters",
            "content": {
                "application/json": {
                    "example": {
                        "uniforms": [
                            "u_time",
                            "u_resolution",
                            "u_backgroundColor",
                            "u_gridSize",
                            "u_gridColor",
                            "u_px",
                            "u_py",
                            "u_r",
                        ],
                        "inputParametersSpec": [
                            {
                                "name": "positionX",
                                "parameter": "u_px",
                                "path": "u_px",
                                "type": "float",
                                "default": 0.0,
                                "min": -1.0,
                                "max": 1.0,
                                "step": 0.01,
                                "smoothingTime": 0.05,
                            },
                            {
                                "name": "radius",
                                "parameter": "u_r",
                                "path": "u_r",
                                "type": "float",
                                "default": 0.5,
                                "min": 0.1,
                                "max": 2.0,
                                "step": 0.01,
                                "smoothingTime": 0.05,
                            },
                        ],
                        "template": {"valid": True, "warnings": []},
                    }
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": [
                                    "body",
                                    "helpers",
                                    "sdHexagon",
                                    "requires",
                                    "inputParametersSpec",
                                    0,
                                    "parameter",
                                ],
                                "msg": "duplicates base parameter 'u_px'",
                                "type": "value_error",
                                "code": "COLLISION_BASE_PARAMETER",
                            }
                        ]
                    }
                }
            },
        },
    },
)
def get_effective_helper(id: int, name: str, db: Session = Depends(get_db)):
    """Return merged uniforms and input parameters for a helper."""
    lib_row = db.query(ShaderLibModel).filter_by(shaderlib_id=id).first()
    if not lib_row:
        raise HTTPException(status_code=404, detail="shader library not found")

    lib_schema = ShaderLibSchema.model_validate(lib_row.definition)

    if name not in lib_schema.helpers:
        raise HTTPException(
            status_code=422,
            detail=[verror(["helpers", name], "helper not found", "HELPER_NOT_FOUND")],
        )

    effective = collect_effective_inputs(lib_schema, name)
    template = check_template_demonstrates_helper(lib_schema, name)
    return {
        "uniforms": effective["uniforms"],
        "inputParametersSpec": effective["inputParametersSpec"],
        "template": template,
    }


__all__ = ["router"]
