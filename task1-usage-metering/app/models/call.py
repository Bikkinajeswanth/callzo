from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class Call(Base):
    """
    Maintains the synchronized state of every telephone call.
    Handles out-of-order event resolution cleanly.
    """
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String(128), unique=True, index=True, nullable=False)
    account_id = Column(String(64), ForeignKey("accounts.id", ondelete="CASCADE"), index=True, nullable=False)
    status = Column(String(32), default="started", index=True, nullable=False)  # started, ended, failed
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0, nullable=False)
    cost_cents = Column(Integer, default=0, nullable=False)
    destination_country = Column(String(8), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    account = relationship("Account", back_populates="calls")

    __table_args__ = (
        Index("ix_calls_account_status", "account_id", "status"),
        Index("ix_calls_account_started_at", "account_id", "started_at"),
    )
