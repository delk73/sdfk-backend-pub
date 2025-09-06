from pydantic import BaseModel, Field
from typing import Union, List, Any, Dict
import uuid


class ErrorDetail(BaseModel):
    # This can be further customized if the list[object] has a specific structure
    # For now, allowing any structure for the objects in the list.
    loc: List[Union[str, int]] = []
    msg: str
    type: str


class ErrorResponse(BaseModel):
    detail: Union[str, List[ErrorDetail], Dict[str, Any]]
    request_id: uuid.UUID = Field(default_factory=uuid.uuid4)
