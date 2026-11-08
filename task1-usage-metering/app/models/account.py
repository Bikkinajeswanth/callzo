from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from app.database.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class Account(Base):
    __tablename__ = "accounts"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=True)
    country = Column(String(8), default="US", nullable=False)
    plan = Column(String(32), default="pro", nullable=False)  # basic, pro, enterprise
    status = Column(String(32), default="active", nullable=False)  # active, trial, suspended
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    calls = relationship("Call", back_populates="account", cascade="all, delete-orphan")
    monthly_usages = relationship("MonthlyUsage", back_populates="account", cascade="all, delete-orphan")
    usage_cap = relationship("UsageCap", back_populates="account", uselist=False, cascade="all, delete-orphan")
    webhook_events = relationship("RawWebhookEvent", back_populates="account", cascade="all, delete-orphan")
