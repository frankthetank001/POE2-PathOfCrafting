from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.models.base import Base


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<AdminUser(username={self.username})>"
