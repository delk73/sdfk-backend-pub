from typing import Optional, List, Dict, Any

from pydantic import BaseModel

# Use permissive external types for nested fields
from synesthetic_schemas.shader import UniformDef, InputParameter


class ShaderAPIResponse(BaseModel):
    """API response model for Shader that includes DB id and
    uses external schema types for nested fields without strict validators.
    """

    shader_id: int
    name: str
    description: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = None
    vertex_shader: str
    fragment_shader: str
    uniforms: Optional[List[UniformDef]] = None
    input_parameters: Optional[List[InputParameter]] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "shader_id": 1,
                    "name": "Example Shader",
                    "vertex_shader": "void main() { gl_Position = vec4(0.0); }",
                    "fragment_shader": "void main() { gl_FragColor = vec4(1.0); }",
                }
            ]
        },
    }

