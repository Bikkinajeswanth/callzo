from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class RawWebhookEvent(Base):
    """
    Stores all raw inbound webhook payloads immutably for auditability,
    replay, idempotency checking, and reconciliation.
    """
    __tablename__ = "raw_webhook_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(128), unique=True, index=True, nullable=False)
    event_type = Column(String(64), index=True, nullable=False)
    account_id = Column(String(64), ForeignKey("accounts.id", ondelete="CASCADE"), index=True, nullable=False)
    call_id = Column(String(128), index=True, nullable=False)
    payload = Column(Text, nullable=False)
    signature = Column(String(256), nullable=True)
    received_at = Column(DateTime, default=utc_now, nullable=False)
    processing_status = Column(String(32), default="processed", index=True, nullable=False)  # processed, duplicate, failed
    error_message = Column(Text, nullable=True)

    account = relationship("Account", back_populates="webhook_events")

    __table_args__ = (
        Index("ix_raw_events_account_type", "account_id", "event_type"),
    )
