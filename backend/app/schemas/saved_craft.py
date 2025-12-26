from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.crafting import CraftableItem


class CraftStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class CraftAction(BaseModel):
    """Represents a single crafting action."""
    currency: str
    omens: List[str] = Field(default_factory=list)


class CraftSubmission(BaseModel):
    """Request schema for submitting a craft for review."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    submitter_name: Optional[str] = Field(None, max_length=255)

    # Craft snapshot data
    initial_item: CraftableItem
    final_item: CraftableItem
    history: List[str]  # Step descriptions
    item_history: List[CraftableItem]  # Item state at each step
    action_history: List[Optional[CraftAction]]  # Action for each step (null for manual edits)
    currency_spent: Dict[str, int]  # Total currency spent
    currency_spent_history: List[Dict[str, int]]  # Currency spent at each step


class CraftUpdate(BaseModel):
    """Request schema for updating a craft (admin only)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    is_featured: Optional[bool] = None
    is_official: Optional[bool] = None


class SavedCraftResponse(BaseModel):
    """Full craft data response."""
    short_id: str
    name: str
    description: Optional[str]
    submitter_name: Optional[str]

    # Craft data
    initial_item: CraftableItem
    final_item: CraftableItem
    history: List[str]
    item_history: List[CraftableItem]
    action_history: List[Optional[Dict[str, Any]]]
    currency_spent: Dict[str, int]
    currency_spent_history: List[Dict[str, int]]

    # Status
    status: CraftStatus
    is_official: bool
    is_featured: bool

    # Stats
    view_count: int
    import_count: int

    # Timestamps
    created_at: datetime
    reviewed_at: Optional[datetime]

    class Config:
        from_attributes = True


class CraftListItem(BaseModel):
    """Lightweight craft info for listings."""
    short_id: str
    name: str
    description: Optional[str]
    submitter_name: Optional[str]

    # Summary info derived from craft data
    base_name: str  # From final_item
    base_category: str
    total_currency_spent: int  # Sum of currency_spent values
    step_count: int  # Length of history

    # Status
    status: CraftStatus
    is_official: bool
    is_featured: bool

    # Stats
    view_count: int
    import_count: int

    # Timestamps
    created_at: datetime

    class Config:
        from_attributes = True


class CraftListResponse(BaseModel):
    """Paginated list of crafts."""
    items: List[CraftListItem]
    total: int
    page: int
    page_size: int


class AdminLoginRequest(BaseModel):
    """Admin login request."""
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    """Admin login response with JWT token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until expiration


class AdminUserResponse(BaseModel):
    """Admin user info response."""
    id: int
    username: str
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True
