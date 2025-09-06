from pydantic import BaseModel, ConfigDict
from typing import Optional


class SchemaBase(BaseModel):
    """Base class for all schema models that map to SQLAlchemy models"""

    model_config = ConfigDict(from_attributes=True)


class ItemBase(SchemaBase):
    name: str
    description: Optional[str] = None


class Item(ItemBase):
    item_id: int
