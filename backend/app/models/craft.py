import secrets
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func

from app.models.base import Base


class CraftStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


def generate_short_id() -> str:
    """Generate an 8-character URL-safe short ID."""
    return secrets.token_urlsafe(6)[:8]


class SavedCraft(Base):
    __tablename__ = "saved_crafts"

    id = Column(Integer, primary_key=True, index=True)
    short_id = Column(String(16), unique=True, index=True, default=generate_short_id)

    # Metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    submitter_name = Column(String(255), nullable=True)

    # Craft data (JSON blobs)
    initial_item = Column(JSON, nullable=False)
    final_item = Column(JSON, nullable=False)
    history = Column(JSON, nullable=False)  # List[str] - step descriptions
    item_history = Column(JSON, nullable=False)  # List[CraftableItem]
    action_history = Column(JSON, nullable=False)  # List[{currency, omens} | null]
    currency_spent = Column(JSON, nullable=False)  # Dict[str, int]
    currency_spent_history = Column(JSON, nullable=False)  # List[Dict[str, int]]

    # Status and visibility
    status = Column(String(20), default=CraftStatus.PENDING.value, index=True)
    is_official = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False, index=True)

    # Stats
    view_count = Column(Integer, default=0)
    import_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    reviewed_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<SavedCraft(short_id={self.short_id}, name={self.name}, status={self.status})>"
