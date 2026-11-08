from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from app.database.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class EventRetryRecord(Base):
    """
    Tracks failed webhook processing for resilient background retries.
    Maintains retry attempts, backoff schedules, and resolution status.
    """
    __tablename__ = "event_retry_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(128), index=True, nullable=False)
    payload = Column(Text, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=5, nullable=False)
    status = Column(String(32), default="pending", index=True, nullable=False)  # pending, in_progress, completed, exhausted
    last_error = Column(Text, nullable=True)
    next_retry_at = Column(DateTime, default=utc_now, index=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index("ix_retries_status_next_retry", "status", "next_retry_at"),
    )
