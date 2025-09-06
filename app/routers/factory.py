from __future__ import annotations

"""Router factory providing CRUD routers for common models."""

from fastapi import Depends

from app.utils.crud_router import create_crud_router
from app import security
from app.models import (
    Tone,
    Haptic,
    Control,
    Modulation,
    Shader,
    ShaderLib,
)
from app.schemas import (
    ToneCreate,
    ToneUpdate,
    Tone as ToneSchema,
    HapticCreate,
    HapticUpdate,
    Haptic as HapticSchema,
    ControlCreate,
    ControlResponse,
    ModulationCreate,
    ModulationUpdate,
    Modulation as ModulationSchema,
    ShaderCreate,
    ShaderUpdate,
    Shader as ShaderSchema,
    ShaderLibCreate,
    ShaderLib as ShaderLibSchema,
)
_dependency = {"dependencies": [Depends(security.verify_jwt)]}

tone_router = create_crud_router(
    Tone,
    ToneCreate,
    ToneUpdate,
    ToneSchema,
    router_kwargs=_dependency,
)

haptic_router = create_crud_router(
    Haptic,
    HapticCreate,
    HapticUpdate,
    HapticSchema,
    router_kwargs=_dependency,
)

control_router = create_crud_router(
    Control,
    ControlCreate,
    ControlCreate,
    ControlResponse,
    router_kwargs=_dependency,
)

modulation_router = create_crud_router(
    Modulation,
    ModulationCreate,
    ModulationUpdate,
    ModulationSchema,
    router_kwargs=_dependency,
)

shader_router = create_crud_router(
    Shader,
    ShaderCreate,
    ShaderUpdate,
    ShaderSchema,
    router_kwargs=_dependency,
)

shader_lib_router = create_crud_router(
    ShaderLib,
    ShaderLibCreate,
    ShaderLibCreate,
    ShaderLibSchema,
    router_kwargs=_dependency,
)


__all__ = [
    "tone_router",
    "haptic_router",
    "control_router",
    "modulation_router",
    "shader_router",
    "shader_lib_router",
]
