from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class UsageCap(Base):
    """
    Configurable monthly caps per account.
    Supports minutes cap and cost cap, with soft or hard enforcement policies.
    """
    __tablename__ = "usage_caps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(64), ForeignKey("accounts.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    monthly_minutes_cap = Column(Integer, nullable=True)  # in minutes (None = unlimited)
    monthly_cost_cents_cap = Column(Integer, nullable=True)  # in cents (None = unlimited)
    is_hard_cap = Column(Boolean, default=True, nullable=False)
    cap_action = Column(String(32), default="flag_exceeded", nullable=False)  # flag_exceeded, alert_only
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    account = relationship("Account", back_populates="usage_cap")
