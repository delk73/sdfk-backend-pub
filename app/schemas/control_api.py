from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ControlAPIResponse(BaseModel):
    control_id: int
    name: str
    description: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = None
    control_parameters: Optional[List[Dict[str, Any]]] = None

    model_config = {
        "from_attributes": True,
        "extra": "ignore",
        "json_schema_extra": {
            "examples": [
                {
                    "control_id": 1,
                    "name": "Example Controls",
                    "control_parameters": [],
                }
            ]
        },
    }
