from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ItemRarity(str, Enum):
    NORMAL = "Normal"
    MAGIC = "Magic"
    RARE = "Rare"
    UNIQUE = "Unique"


class ItemSocket(BaseModel):
    group: int
    attr: Optional[str] = None


class ItemMod(BaseModel):
    text: str
    values: List[str] = Field(default_factory=list)


class ParsedItem(BaseModel):
    rarity: ItemRarity
    name: str
    base_type: str
    item_level: Optional[int] = None
    quality: Optional[int] = None
    sockets: List[ItemSocket] = Field(default_factory=list)
    requirements: Dict[str, int] = Field(default_factory=dict)
    implicits: List[ItemMod] = Field(default_factory=list)
    explicits: List[ItemMod] = Field(default_factory=list)
    corrupted: bool = False
    identified: bool = True
    raw_text: str


class ItemParseRequest(BaseModel):
    item_text: str = Field(..., min_length=1)


class ItemParseResponse(BaseModel):
    success: bool
    item: Optional[ParsedItem] = None
    error: Optional[str] = None